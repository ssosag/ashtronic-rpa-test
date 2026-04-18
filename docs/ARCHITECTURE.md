# Arquitectura

Descripción textual de la arquitectura de la solución: modelo de datos, servicios, flujo del bot, secuencia del endpoint de extracción y pantallas del frontend.

---

## 1. Modelo de datos (ERD textual)

Dos entidades con relación **1:N**:

- **`jobs`** — una ejecución del bot.
  - `id` (PK), `status` (`queued | running | done | error`), `fecha_inicial`, `fecha_final`, `limit`.
  - Marcas de tiempo: `created_at`, `started_at`, `finished_at`.
  - `records_count` (cacheado para evitar `COUNT(*)` en el listado del frontend).
  - `error_message` (texto libre cuando `status='error'`).

- **`records`** — una fila extraída del portal.
  - `id` (PK), `job_id` (FK → `jobs.id`, `ON DELETE CASCADE`).
  - Campos normalizados: `patient_name`, `patient_document`, `date_service`, `sede`, `contrato`, `external_row_id`.
  - `raw_row_json` (JSONB) con la fila completa del portal para trazabilidad.
  - `captured_at`.

Índices: `ix_records_job_id`, `ix_records_patient_document`.

Justificación del modelo en [`DECISIONES_TECNICAS.md#d13`](./DECISIONES_TECNICAS.md#d13--modelos-job-1--n-record-con-raw_row_json).

---

## 2. Arquitectura de despliegue

Cuatro servicios definidos en `docker-compose.yml`:

| Servicio | Imagen | Puerto | Rol |
|---|---|---|---|
| `frontend` | Nginx sirviendo el build de React | `5173 → 80` | UI de monitoreo |
| `api` | Python 3.12 slim + FastAPI | `8000` | Endpoints + orquestación del bot |
| `db` | `postgres:16-alpine` | `5432` | Persistencia |
| `selenium` | `selenium/standalone-chrome:latest` | `4444`, `7900` | WebDriver remoto + noVNC |

Conexiones:

- `frontend → api`: HTTP a `/api/v1/*`.
- `api → db`: `asyncpg` sobre TCP.
- `api → selenium`: HTTP WebDriver protocol contra `http://selenium:4444/wd/hub`.
- `selenium → Portal Hiruko`: HTTPS externo (única conexión saliente a internet).

---

## 3. Flujo funcional del bot

Secuencia ejecutada por `app/rpa/bot.py`. Cada paso es un módulo en [`app/rpa/steps/`](../app/rpa/steps/):

1. **`driver.py`** — abrir `webdriver.Remote` contra el hub de Selenium.
2. **`steps/login.py`** — navegar a `/login`, rellenar usuario/password, esperar la redirección al dashboard.
3. **`steps/navigate.py`** — abrir menú **Facturación → Generar Factura**.
4. **`steps/filters.py`** — aplicar filtros obligatorios:
   - Convenio = `Savia Salud Subsidiado`
   - Contrato = el correspondiente (depende del convenio; esperar a que el `<select>` se pueble)
   - Sedes = todas
   - Modalidad = `US`
   - Fechas = `fecha_inicial`, `fecha_final`
5. **`steps/extract.py`** — click en **Buscar**, esperar a que desaparezca el overlay (`blockUI`), esperar la presencia del `tbody` (la tabla se renderiza dinámicamente tras el primer click) e iterar las filas hasta `min(limit, filas_disponibles)`.

Convenciones transversales:

- **Esperas explícitas**, nunca `sleep` como mecanismo primario ([D15](./DECISIONES_TECNICAS.md#d15--esperas-explícitas--validación-de-cambio-de-tabla)).
- En caso de fallo, el orquestador captura la excepción, guarda un screenshot ([D16](./DECISIONES_TECNICAS.md#d16--screenshots-automáticos-en-errores-del-bot)) y propaga una excepción definida en `app/rpa/errors.py`.

---

## 4. Secuencia del endpoint `/rpa/extract`

1. El usuario envía el formulario en **Nueva extracción**.
2. El frontend llama `POST /api/v1/rpa/extract`.
3. La API:
   - Valida el payload con Pydantic (`limit > 0`, `fecha_inicial ≤ fecha_final`).
   - `INSERT` en `jobs` con `status='queued'`.
   - Programa una `BackgroundTask` (`rpa_runner.run(job_id)`).
   - Responde `202 Accepted` con `{ job_id, status, message }`.
4. La `BackgroundTask` (en una sesión async independiente):
   - `UPDATE jobs SET status='running', started_at=NOW()`.
   - Ejecuta `bot.run(params)` (Selenium contra el portal).
   - Bulk-insert de los `Record` extraídos y `UPDATE jobs SET status='done'` en una única transacción (`async with db.begin()`).
   - En error: `mark_error` guarda `status='error'`, `error_message` y screenshot en disco.
5. El frontend hace polling `GET /api/v1/jobs/{id}` cada 2 segundos hasta recibir un estado terminal (`done`/`error`). El polling se cancela con `AbortController` al desmontar o cambiar de job.
6. Al arrancar la API, `recover_orphan_jobs` marca como `error` cualquier job que quedó en `queued`/`running` (ej. crash del contenedor mid-extracción).

---

## 5. Pantallas del frontend

| Pantalla | Ruta | Contenido |
|---|---|---|
| Nueva extracción | `/` | Formulario con `fecha_inicial`, `fecha_final`, `limit`. Validación: fechas entre 2000 y 2100, `limit` entero > 0 (sin tope superior). Tras submit redirige a `/jobs/{id}`. |
| Jobs | `/jobs` | Tabla con `id`, `status` (badge), `fecha_inicial`, `fecha_final`, `limit`, `records_count`. Click en fila → detalle. |
| Job detail | `/jobs/:id` | Parámetros del job + polling cada 2s. Muestra los `records` asociados con paginación (10/25/50/100) y botón "Descargar CSV" (página actual). |
| Records | `/records` | Tabla global con filtros `patient_document`, `patient_name`, `sede`. Misma paginación + CSV. |

**Paleta Tailwind:**

| Rol | Color |
|---|---|
| `brand` (primario) | `#2563eb` |
| `status-done` | `#16a34a` |
| `status-running` | `#0ea5e9` |
| `status-queued` | `#eab308` |
| `status-error` | `#dc2626` |
| Fondo | `#f9fafb` |
| Texto | `#111827` |
