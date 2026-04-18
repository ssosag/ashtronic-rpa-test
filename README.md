# Ashtronic RPA Test — Prueba técnica Santiago Sosa

> Solución end-to-end RPA + Backend + Base de datos + Frontend de monitoreo para extraer registros de facturación del portal Hiruko Prodiagnóstico.

---

## 1. Descripción general

El sistema automatiza la extracción de filas del módulo **Facturación → Generar Factura** del portal Hiruko. El usuario dispara una extracción desde un frontend React indicando `fecha_inicial`, `fecha_final` y `limit`; la API FastAPI encola un job, un bot Selenium inicia sesión en el portal, aplica los filtros obligatorios (**Convenio: Savia Salud Subsidiado**, contrato correspondiente, sedes: todas, modalidad: US), lee la tabla de resultados fila por fila y persiste cada una en PostgreSQL asociada al job. El frontend hace polling del estado del job cada 2s hasta que termine y permite ver/descargar los registros en CSV.

## 2. Arquitectura

Cuatro servicios orquestados con Docker Compose:

| Servicio | Rol | Imagen |
|---|---|---|
| `frontend` | SPA React servida por Nginx | `./frontend` (multi-stage) |
| `api` | FastAPI + SQLAlchemy async + BackgroundTasks | `./` (Python 3.12-slim) |
| `db` | PostgreSQL | `postgres:16-alpine` |
| `selenium` | Chrome headless + WebDriver | `selenium/standalone-chrome:latest` |

Descripción detallada de servicios, modelo de datos y flujo del bot en [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

```
┌──────────┐      HTTP JSON     ┌──────────┐    asyncpg    ┌───────┐
│ frontend │ ─────────────────► │   api    │ ────────────► │  db   │
│  React   │ ◄───────────────── │ FastAPI  │               │ PG 16 │
└──────────┘    poll 2s         └────┬─────┘               └───────┘
                                     │ BackgroundTask
                                     ▼
                                ┌──────────┐    HTTPS     ┌──────────────┐
                                │ selenium │ ───────────► │ Portal Hiruko│
                                │  chrome  │              └──────────────┘
                                └──────────┘
```

## 3. Estructura de carpetas

```
ashtronic-rpa-test/
├── app/                       # Backend FastAPI
│   ├── api/v1/                # Routers: health, rpa, jobs, records
│   ├── core/                  # config (Pydantic Settings), logging
│   ├── db/                    # database.py (engine lazy), models.py
│   ├── rpa/                   # driver, waits, errors, steps/
│   │   └── steps/             # login, navigate, filters, extract
│   ├── schemas/               # Pydantic v2 (ExtractRequest, JobOut, RecordOut…)
│   ├── services/              # job_service, rpa_runner
│   └── main.py                # App + lifespan (recover_orphan_jobs al inicio)
├── frontend/                  # React 18 + Vite 5 + TS + Tailwind
│   └── src/
│       ├── api/               # client.ts, types.ts
│       ├── components/        # StatusBadge
│       ├── hooks/             # useJobPolling (AbortController)
│       ├── lib/               # csv.ts + csv.test.ts
│       └── pages/             # NewExtraction, JobsList, JobDetail, RecordsList
├── tests/                     # pytest + httpx + aiosqlite in-memory
├── docs/                      # DECISIONES_TECNICAS, ARCHITECTURE
├── .github/workflows/ci.yml   # pytest + frontend lint/format/test/build
├── docker-compose.yml
├── Dockerfile                 # backend
├── requirements.txt / requirements-dev.txt
├── pytest.ini
└── .env.example
```

## 4. Prerrequisitos

- Docker Desktop (o Docker Engine + Docker Compose v2)
- Git
- Credenciales del portal Hiruko Prodiagnóstico

Para desarrollo local sin Docker (opcional): Python 3.12 y Node.js 20+.

## 5. Variables de entorno

Copiar `.env.example` a `.env` y completar credenciales. **Ningún secreto vive en el repositorio.**

| Variable | Propósito | Ejemplo |
|---|---|---|
| `PORTAL_URL` | URL base del portal | `https://prodiagnosticotest.hiruko.com.co` |
| `PORTAL_USER` | Usuario del portal | `ASHTRONIC` |
| `PORTAL_PASSWORD` | Contraseña del portal | `********` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciales PG | `ashtronic/ashtronic/ashtronic_rpa` |
| `DATABASE_URL` | DSN async para SQLAlchemy | `postgresql+asyncpg://ashtronic:ashtronic@db:5432/ashtronic_rpa` |
| `SELENIUM_HUB_URL` | Endpoint WebDriver remoto | `http://selenium:4444/wd/hub` |
| `SELENIUM_TIMEOUT` | Timeout global de esperas (s) | `30` |
| `BOT_RETRY_ATTEMPTS` | Intentos totales en login/extract (1 = sin retry) | `3` |
| `BOT_RETRY_BACKOFF_SECONDS` | Backoff base para reintentos transitorios | `2.0` |
| `SCREENSHOTS_DIR` | Carpeta de screenshots en error | `/app/artifacts/screenshots` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_JSON` | Si `true`, emite logs JSON con `request_id` incluido | `false` |

## 6. Cómo levantar la solución

```bash
cp .env.example .env         # completar credenciales del portal
docker compose up --build
```

URLs:

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Selenium console (noVNC) | http://localhost:7900 (password `secret`) |

Para parar:

```bash
docker compose down          # conserva datos
docker compose down -v       # borra el volumen de Postgres
```

### Inicialización del esquema de BD

El esquema se crea al arranque de la API llamando `Base.metadata.create_all` dentro del `lifespan` (ver `app/main.py`). Es reproducible (`docker compose down -v && docker compose up --build` regenera todo desde cero) y determinístico: los modelos en `app/db/models.py` son la única fuente de verdad del esquema. Para una prueba con un modelo estable, Alembic sería overhead; en producción la migración sería el siguiente paso (§11.7).

## 7. Cómo probar los endpoints

Todos los endpoints están bajo `/api/v1`. Doc interactiva en `/docs`.

### Disparar una extracción

PowerShell:

```powershell
curl -X POST http://localhost:8000/api/v1/rpa/extract `
  -H 'Content-Type: application/json' `
  -d '{"fecha_inicial":"2026-03-01","fecha_final":"2026-03-31","limit":20}'
```

bash/zsh:

```bash
curl -X POST http://localhost:8000/api/v1/rpa/extract \
  -H 'Content-Type: application/json' \
  -d '{"fecha_inicial":"2026-03-01","fecha_final":"2026-03-31","limit":20}'
```

Respuesta `202`:

```json
{ "job_id": 1, "status": "queued", "message": "Extraction queued" }
```

### Catálogo

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/health` | Health check. |
| `POST` | `/rpa/extract` | Encola una extracción. Valida `limit > 0`, `fecha_inicial ≤ fecha_final`. Devuelve `202` + `job_id`. |
| `GET`  | `/jobs?skip=&limit=` | Lista jobs por `created_at DESC`. `limit` máx 100. |
| `GET`  | `/jobs/{id}` | Detalle de un job. `404` si no existe. |
| `GET`  | `/records?job_id=&patient_document=&patient_name=&sede=&skip=&limit=` | Lista registros con filtros `ILIKE` parciales. `limit` máx 500. |
| `GET`  | `/records/{id}` | Detalle del registro + `raw_row_json`. |

## 8. Cómo usar el frontend

Cuatro rutas principales (React Router):

1. **Nueva extracción** (`/`) — formulario con validación: fechas entre 2000 y 2100, `limit` entero positivo (sin tope superior). Al enviar, navega al detalle del job creado.
2. **Jobs** (`/jobs`) — tabla con estado, fechas, `limit`, `records_count`. Click en una fila abre el detalle.
3. **Detalle de Job** (`/jobs/:id`) — polling cada 2s mientras el estado sea `queued`/`running`. Muestra los registros asociados con paginación (10/25/50/100) y botón **Descargar CSV** (página actual). Si el job terminó en `error`, muestra `error_message`.
4. **Records** (`/records`) — tabla global con filtros por `patient_document`, `patient_name` y `sede`. Misma paginación + CSV.

Paleta Tailwind: `brand` (primario `#2563eb`) + `status-{done,running,queued,error}` para los badges.

## 9. Flujo general del sistema

1. Usuario envía el formulario → `POST /api/v1/rpa/extract`.
2. `job_service.create_job` inserta un `Job(status="queued")`; la API responde `202` con `job_id` y encola una `BackgroundTask` (`rpa_runner.run(job_id)`).
3. `rpa_runner` abre su propia sesión async, marca el job como `running`, instancia un WebDriver remoto contra `SELENIUM_HUB_URL` y ejecuta los pasos en orden: `login → navigate → filters → extract`.
4. `extract_rows` hace click en **Buscar**, espera a que desaparezca el overlay `blockUI`, espera la presencia del `tbody` (la tabla se renderiza dinámicamente tras el primer click) y lee las filas hasta `min(limit, filas_disponibles)`.
5. Las filas se insertan en una única transacción (`async with db.begin()`) junto con el `UPDATE Job SET status='done'`. En error: `logger.exception` captura el traceback, `mark_error` deja el job en `error` con `error_message` + screenshot en `artifacts/screenshots/`.
6. El frontend hace polling de `/jobs/:id` hasta que `status ∈ {done, error}`. El polling se cancela con `AbortController` al desmontar o cambiar de job.
7. Al arrancar la API, `recover_orphan_jobs` marca como `error` cualquier job que quedó en `queued`/`running` (ej. crash del contenedor mid-extracción).

## 10. Extracción de datos — campos persistidos y justificación

Por cada fila extraída del portal se guarda en la tabla `records`:

| Campo | Tipo | Justificación |
|---|---|---|
| `external_row_id` | `str?` | Identificador visible en la tabla del portal. Permite trazar una fila de BD a su origen sin depender de `id` interno. |
| `patient_name` | `str?` | Nombre del paciente. Campo central del negocio; usado en filtros del frontend. |
| `patient_document` | `str?` | Documento. Clave funcional más utilizada para búsquedas. Lleva índice. |
| `date_service` | `str` | Fecha/hora del servicio tal como la muestra el portal. Se guarda como string para evitar suposiciones de formato y preservar el valor exacto (el portal puede devolver `YYYY-MM-DD HH:MM:SS`). |
| `sede` | `str?` | Sede del servicio. Filtro del frontend. |
| `contrato` | `str?` | Contrato/convenio asociado. |
| `raw_row_json` | `JSONB` | Fila completa con **todas** las columnas visibles del portal. Garantiza trazabilidad total aunque añadamos o eliminemos columnas normalizadas. |
| `captured_at` | `datetime` | Timestamp del momento de inserción en BD. |
| `job_id` | `FK` | Enlace al `Job` que la extrajo (`ON DELETE CASCADE`). |

**Criterio:** normalizamos los campos que el frontend necesita filtrar u ordenar; el resto vive en `raw_row_json` para no perder información y no acoplarse a cambios de layout del portal.

## 11. Robustez del bot

Cumplimiento explícito de las consideraciones obligatorias del PDF (§4):

- **Esperas explícitas, no `sleep`.** Todas las esperas usan `WebDriverWait + expected_conditions` en `app/rpa/waits.py`: `wait_present`, `wait_visible`, `wait_clickable`, `wait_not_disabled`, `wait_select_populated`, `wait_overlay_gone`. No hay `time.sleep` como mecanismo primario.
- **Validación del cambio de tabla.** Tras click en **Buscar**, `extract_rows` espera a que desaparezca el overlay `blockUI` **y** a que aparezca el `tbody` — la tabla se renderiza dinámicamente solo tras la primera búsqueda, por lo que validamos presencia real y no solo ausencia de overlay.
- **Timeouts controlados.** `SELENIUM_TIMEOUT` (env, default 30s) aplica globalmente; cada helper acepta override por paso. El timeout levanta `TimeoutException`, capturada por el orquestador.
- **Manejo de errores.** `app/rpa/errors.py` define excepciones por fase (`LoginError`, `NavigationError`, `ExtractionError`). El runner captura, hace `logger.exception` (incluye traceback), guarda screenshot en `SCREENSHOTS_DIR` y marca el job como `error` con el mensaje.
- **Logs trazables.** Cada paso loggea con un formato consistente: `step=<fase> action=<acción>`; ej. `step=extract action=click_buscar`, `step=filters action=select_convenio value=...`. Permite grep por fase o por acción. Con `LOG_JSON=true` los logs salen en JSON por línea e incluyen un `request_id` propagado vía middleware (se puede forzar vía header `X-Request-ID`) — listo para enviar a Datadog / CloudWatch / Loki.
- **Selectores estables.** Ids (`#detalle_consulta`, `#btn-buscar`) cuando existen; de lo contrario, clases semánticas (`.blockUI`, `.dataTables_processing`). Los selectores viven centralizados por paso, no dispersos.
- **Reintentos controlados.** Los pasos `login` y `extract` se reintentan con backoff exponencial (`app/rpa/retry.py`) ante errores transitorios (`TimeoutException`, `WebDriverException`) — útil cuando el portal responde lento o el overlay `blockUI` se queda un momento pegado. Los errores estructurales **no** se reintentan: `InvalidCredentialsError` (el portal rechaza credenciales) aborta inmediatamente, porque reintentar es desperdicio. Configurable vía `BOT_RETRY_ATTEMPTS` (default 3) y `BOT_RETRY_BACKOFF_SECONDS` (default 2.0).

## 12. Checklist de verificación en local

- [ ] `cp .env.example .env` y completar credenciales reales
- [ ] `docker compose up --build` arranca sin errores
- [ ] `GET http://localhost:8000/api/v1/health` → `200`
- [ ] `http://localhost:7900` (password `secret`) muestra la pantalla de Chrome headless
- [ ] `http://localhost:5173` carga el frontend
- [ ] Una extracción pequeña (`limit=5`) termina en `done`
- [ ] Los registros aparecen en `/records` y pueden descargarse como CSV

## 13. Tests

Backend (pytest + aiosqlite in-memory):

```bash
pip install -r requirements-dev.txt
pytest
```

Cubre: validación de schemas, endpoints (`/rpa/extract`, `/jobs`, `/records`), `job_service` (`recover_orphan_jobs`, filtros), helpers de esperas (`wait_overlay_gone` con mocks).

Frontend (vitest + @testing-library/react, jsdom):

```bash
cd frontend && npm install && npm test
```

Cubre:
- `lib/csv.ts` — escape de comas/comillas/newlines, null/undefined, header.
- `components/StatusBadge` — labels en español por cada estado.
- `pages/NewExtraction` — validación (limit=0, rango invertido), submit exitoso + navegación.
- `pages/JobsList` — loading / empty / render de filas / error del API.
- `pages/RecordDetail` — campos normalizados + `raw_row_json` pretty-printed.

CI: `.github/workflows/ci.yml` ejecuta ambos en cada push/PR, más `eslint`, `prettier --check` y `vite build`.

## 14. Análisis técnico

El análisis técnico requerido por el enunciado (por qué esta arquitectura, ventajas, desventajas, decisiones por simplicidad/tiempo, qué mejoraría, cómo escalaría, qué faltaría para producción, evolución futura) se encuentra en [`docs/DECISIONES_TECNICAS.md`](./docs/DECISIONES_TECNICAS.md#análisis-técnico-preguntas-obligatorias-del-enunciado), junto con el registro detallado de cada decisión individual (D01–D17).

---

## Documentación complementaria

- [`docs/DECISIONES_TECNICAS.md`](./docs/DECISIONES_TECNICAS.md) — decisiones técnicas + análisis técnico obligatorio.
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — descripción de servicios, modelo de datos, flujo del bot y secuencia de la extracción.
- [`docs/OPERACION.md`](./docs/OPERACION.md) — comandos útiles (logs, ver reintentos, DB, screenshots, curl).
