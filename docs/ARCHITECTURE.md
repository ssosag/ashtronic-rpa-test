# Arquitectura

Este documento describe la arquitectura de la solución con 5 diagramas. Las imágenes viven en [`./images/`](./images/) y son exportadas desde el archivo Figma del proyecto.

> **Estado de los diagramas:** 🚧 en construcción durante Fase 0. Este archivo actúa de índice y explica cada diagrama en prosa mientras Figma se cierra.

---

## 1. Diagrama entidad-relación (ERD)

![ERD](./images/erd.png)

**Explicación.**

Dos entidades con relación **1:N**:

- **`jobs`** representa una ejecución del bot. Guarda los parámetros de entrada (`fecha_inicial`, `fecha_final`, `limit`), el estado (`queued | running | done | error`), marcas de tiempo (`started_at`, `finished_at`) y un contador cacheado (`records_count`) para evitar `COUNT(*)` en el listado del frontend.
- **`records`** representa una fila extraída del portal. Incluye campos normalizados (`patient_name`, `patient_document`, `sede`, `contrato`, `date_service`) y un campo `raw_row_json` (JSONB) con la fila completa para trazabilidad.
- `records.job_id` es FK a `jobs.id` con `ON DELETE CASCADE` e índice para el filtro por job.
- Índice adicional sobre `records.patient_document` para búsqueda en el frontend.

Justificación del modelo en [`DECISIONES_TECNICAS.md#d13`](./DECISIONES_TECNICAS.md#d13--modelos-job-1--n-record-con-raw_row_json).

---

## 2. Arquitectura de despliegue

![Arquitectura](./images/architecture.png)

**Explicación.**

Cuatro servicios en `docker-compose.yml`:

| Servicio | Imagen | Puerto | Rol |
|---|---|---|---|
| `frontend` | Nginx sirviendo React build | `80` | UI de monitoreo |
| `api` | Python 3.12 slim + FastAPI | `8000` | Endpoints + orquestación del bot |
| `db` | `postgres:16-alpine` | `5432` | Persistencia |
| `selenium` | `selenium/standalone-chrome:latest` | `4444`, `7900` | WebDriver remoto + noVNC |

Conexiones:

- `frontend → api`: HTTP al path `/api/v1/*` (Nginx reverse proxy).
- `api → db`: `asyncpg` sobre TCP.
- `api → selenium`: HTTP WebDriver protocol contra `http://selenium:4444/wd/hub`.
- `selenium → Portal Hiruko`: HTTPS externo (única conexión saliente a internet).

---

## 3. Flujo funcional del bot

![Flujo del bot](./images/bot-flow.png)

**Explicación (pasos secuenciales, cada uno es un módulo en [`app/rpa/steps/`](../app/rpa/steps/)):**

1. **`driver.py`** — abrir `webdriver.Remote` contra el hub.
2. **`steps/login.py`** — navegar a `/login`, rellenar usuario/password, esperar la redirección al dashboard.
3. **`steps/navigate.py`** — abrir menú **Facturación → Generar Factura**.
4. **`steps/filters.py`** — aplicar filtros obligatorios:
   - Convenio = `Savia Salud Subsidiado`
   - Contrato = el correspondiente (depende del convenio, esperar que el `<select>` se pueble)
   - Sedes = todas
   - Modalidad = `US`
   - Fechas = `fecha_inicial`, `fecha_final`
5. **`steps/extract.py`** — click en **Buscar**, `wait_table_refreshed`, iterar filas hasta `min(limit, filas_disponibles)`.

Todos los steps:
- Usan **esperas explícitas**, no sleeps ([D15](./DECISIONES_TECNICAS.md#d15--esperas-explícitas--validación-de-cambio-de-tabla)).
- Al fallar, el orquestador `bot.py` captura, guarda screenshot ([D16](./DECISIONES_TECNICAS.md#d16--screenshots-automáticos-en-errores-del-bot)) y propaga una excepción del módulo `app/rpa/errors.py`.

---

## 4. Diagrama de secuencia — flujo del endpoint `/rpa/extract`

![Secuencia extract](./images/sequence-extract.png)

**Explicación.**

1. El usuario hace submit en **Nueva extracción**.
2. El frontend llama `POST /api/v1/rpa/extract`.
3. La API:
   - Valida el payload con Pydantic.
   - `INSERT` en `jobs` con status `queued`.
   - Programa una `BackgroundTask` (`rpa_runner.run(job_id)`).
   - Responde `202 Accepted` con `{job_id, status}`.
4. La `BackgroundTask`:
   - `UPDATE jobs SET status='running', started_at=NOW()`.
   - Ejecuta `bot.run(params)` (Selenium contra el portal).
   - Por cada fila extraída: `INSERT INTO records`.
   - Al terminar: `UPDATE jobs SET status='done', finished_at=NOW(), records_count=N`.
   - En error: `UPDATE jobs SET status='error', error_message=…, finished_at=NOW()` + screenshot en disco.
5. El frontend hace polling `GET /api/v1/jobs/{id}` cada `POLL_INTERVAL_SECONDS` hasta recibir un estado terminal.

---

## 5. Wireframes de las 3 pantallas

![Wireframes](./images/wireframes.png)

**Explicación.**

| Pantalla | Ruta | Contenido |
|---|---|---|
| Nueva extracción | `/` o `/new` | Formulario con `fecha_inicial`, `fecha_final`, `limit`, botón "Ejecutar". Tras submit redirige a `/jobs/{id}`. |
| Jobs | `/jobs` | Tabla con `id`, `status` (badge), `started_at`, `finished_at`, `records_count`. Auto-refresh cada `POLL_INTERVAL_SECONDS`. Click en fila → detalle. |
| Job detail | `/jobs/{id}` | Parámetros del job, estado, `error_message` si aplica, link a "Ver registros de este job". |
| Records | `/records` | Tabla de records con filtros por `job_id` y `patient_document`. Paginación. |
| Record detail | `/records/{id}` | Campos normalizados + bloque `<pre>` con `raw_row_json`. |

**Paleta:**

| Rol | Color |
|---|---|
| Primario | `#2563eb` |
| `done` | `#16a34a` |
| `running` | `#0ea5e9` |
| `queued` | `#eab308` |
| `error` | `#dc2626` |
| Fondo | `#f9fafb` |
| Texto | `#111827` |
