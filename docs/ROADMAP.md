# Roadmap de construcción

Plan de construcción de la solución en 11 fases (0 → 10). Cada fase tiene **objetivo**, **entregables concretos**, **commit asociado** (en [Conventional Commits](./DECISIONES_TECNICAS.md#d17--conventional-commits)) y **riesgos técnicos** identificados de antemano.

## Leyenda de estado

- ✅ Completada
- 🟡 En curso
- ⚪ Pendiente

---

## Resumen

| # | Fase | Objetivo | Commit | Estado |
|---|---|---|---|---|
| 0 | [Bootstrap](#fase-0-bootstrap) | Scaffolding, decisiones técnicas, diagramas Figma | `chore: bootstrap project scaffolding and technical decisions` | 🟡 |
| 1 | [Backend skeleton](#fase-1-backend-skeleton) | FastAPI app + settings + logging + `/health` | `feat(backend): fastapi app skeleton with health endpoint` | ⚪ |
| 2 | [DB y modelos](#fase-2-db-y-modelos) | SQLAlchemy async + `Job`, `Record` + schemas Pydantic | `feat(db): job and record models with async sqlalchemy` | ⚪ |
| 3 | [Endpoints (stub)](#fase-3-endpoints-stub) | `/rpa/extract`, `/jobs`, `/records` con bot stub | `feat(api): rpa, jobs and records endpoints with background tasks` | ⚪ |
| 4 | [Docker base](#fase-4-docker-base) | `Dockerfile` API + `docker-compose.yml` (4 servicios) | `feat(docker): compose with api, db and selenium services` | ⚪ |
| 5 | [Bot RPA real](#fase-5-bot-rpa-real) | `app/rpa/*` con esperas explícitas y screenshots | varios `feat(rpa): …` | ⚪ |
| 6 | [Frontend](#fase-6-frontend) | React + 3 pantallas + polling + Nginx | `feat(frontend): monitoring ui with new-extraction, jobs, records pages` | ⚪ |
| 7 | [Tests mínimos](#fase-7-tests-mínimos) | Smoke API, validación schemas, helpers del bot | `test: smoke tests for api and rpa helpers` | ⚪ |
| 8 | [README final](#fase-8-readme-final) | 11 secciones + 7 respuestas del análisis técnico | `docs: final readme with architecture and technical analysis` | ⚪ |
| 9 | [BONUS observabilidad](#fase-9-bonus-observabilidad) | Logs JSON, `request_id`, retry policy | `feat(observability): structured logging and retry policy` | ⚪ |
| 10 | [BONUS despliegue AWS](#fase-10-bonus-despliegue-aws) | Terraform ECS Fargate + RDS + ALB + ECR | `feat(infra): terraform for aws fargate deployment` | ⚪ |

---

## Fase 0: Bootstrap

**Estado:** 🟡 En curso

**Objetivo.** Dejar el repositorio con todos los artefactos base, las decisiones técnicas documentadas, los diagramas arquitectónicos diseñados en Figma, y el README con su esqueleto de 11 secciones. Ninguna línea de código de aplicación aún.

**Entregables.**

- `.gitignore`, `.dockerignore`, `.env.example`
- `requirements.txt` con las dependencias base de Python
- `README.md` — esqueleto con las 11 secciones del enunciado (puntos 1–11)
- `docs/DECISIONES_TECNICAS.md` — 17 decisiones iniciales documentadas con *qué*, *por qué*, *consecuencias*
- `docs/ARCHITECTURE.md` — índice de los 5 diagramas con explicación en prosa
- `docs/ROADMAP.md` — este archivo
- `docs/images/.gitkeep` — placeholder para las 5 imágenes exportadas desde Figma
- `artifacts/screenshots/.gitkeep` — placeholder para los snapshots que el bot guardará en errores
- **Diagramas en Figma** (exportados a `docs/images/`): `erd.png`, `architecture.png`, `bot-flow.png`, `sequence-extract.png`, `wireframes.png`

**Commit.** `chore: bootstrap project scaffolding and technical decisions`

**Riesgos.** Ninguno técnico. Riesgo humano: inconsistencia entre decisiones tomadas y lo implementado en fases posteriores → se mitiga manteniendo `DECISIONES_TECNICAS.md` como fuente de verdad viva.

---

## Fase 1: Backend skeleton

**Estado:** ⚪ Pendiente

**Objetivo.** Levantar una app FastAPI que arranque, configure logging, lea settings desde `.env` y responda a `GET /api/v1/health`. Sin DB ni bot todavía.

**Entregables.**

- `app/__init__.py`
- `app/main.py` — `FastAPI(...)`, `lifespan`, `CORSMiddleware`, `include_router`
- `app/core/__init__.py`
- `app/core/config.py` — `Settings(BaseSettings)` con `get_settings()` cacheado
- `app/core/logging.py` — `configure_logging(level)` con formato plano ([D05](./DECISIONES_TECNICAS.md#d05--logging-plano-en-fase-1-estructurado-json-en-fase-9-bonus))
- `app/api/__init__.py`
- `app/api/v1/__init__.py`
- `app/api/v1/router.py` — agregador de sub-routers
- `app/api/v1/health.py` — `GET /health`

**Commit.** `feat(backend): fastapi app skeleton with health endpoint`

**Riesgos.**
- Nombres de variables `.env` inconsistentes con lo que espera `pydantic-settings` → se mitiga con prefijos claros y con `model_config = SettingsConfigDict(env_file=".env")`.

**Validación manual al cerrar la fase.**
- `uvicorn app.main:app --reload` arranca sin errores
- `GET http://localhost:8000/api/v1/health` responde `{"status":"healthy"}`
- `GET http://localhost:8000/docs` muestra Swagger

---

## Fase 2: DB y modelos

**Estado:** ⚪ Pendiente

**Objetivo.** Modelos SQLAlchemy async para `Job` y `Record`, schemas Pydantic de request/response, y creación automática del schema con `Base.metadata.create_all` en el `lifespan` ([D03](./DECISIONES_TECNICAS.md#d03--migraciones-sqlalchemycreate_all-en-el-startup-sin-alembic)).

**Entregables.**

- `app/db/__init__.py`
- `app/db/database.py` — `engine`, `async_session`, `get_db`, `init_db`, `close_db`
- `app/db/models.py` — `Job`, `Record` ([D13](./DECISIONES_TECNICAS.md#d13--modelos-job-1--n-record-con-raw_row_json), [D14](./DECISIONES_TECNICAS.md#d14--estados-del-job-queued--running--done--error))
- `app/schemas/__init__.py`
- `app/schemas/rpa.py` — `ExtractRequest`, `ExtractResponse`
- `app/schemas/jobs.py` — `JobStatus` enum, `JobOut`, `JobDetail`
- `app/schemas/records.py` — `RecordOut`, `RecordDetail`, `RecordFilters`
- `app/main.py` — actualizar `lifespan` para llamar `init_db()` / `close_db()`

**Commit.** `feat(db): job and record models with async sqlalchemy`

**Riesgos.**
- `DATABASE_URL` con esquema `postgresql://` (no `postgresql+asyncpg://`) → normalizar en `config.py` con un `model_validator`.
- Pydantic v2 desconfigurado con ORM: usar `model_config = ConfigDict(from_attributes=True)` en los schemas de output.

**Validación manual al cerrar la fase.**
- `psql` al contenedor `db` muestra tablas `jobs` y `records` tras reiniciar la API
- `GET http://localhost:8000/docs` muestra los schemas Pydantic en la sección de modelos

---

## Fase 3: Endpoints (stub)

**Estado:** ⚪ Pendiente

**Objetivo.** Exponer todos los endpoints que exige el enunciado con lógica real de persistencia, pero con un **stub** en lugar del bot Selenium (el stub inserta 2 records fake con `time.sleep(3)` simulado). Esto desbloquea el frontend y el contrato API.

**Entregables.**

- `app/api/deps.py` — `get_db` dependency
- `app/api/v1/rpa.py` — `POST /rpa/extract` con `BackgroundTasks` ([D10](./DECISIONES_TECNICAS.md#d10--ejecución-asíncrona-del-bot-con-backgroundtasks))
- `app/api/v1/jobs.py` — `GET /jobs`, `GET /jobs/{id}`
- `app/api/v1/records.py` — `GET /records` (filtros `job_id`, `patient_document`), `GET /records/{id}` ([D06](./DECISIONES_TECNICAS.md#d06--bonus-ux-incluidos-desde-el-inicio-en-el-frontend))
- `app/services/__init__.py`
- `app/services/rpa_runner.py` — orquestador con **stub** del bot
- `app/services/job_service.py` — queries reutilizables sobre `Job`/`Record`
- `app/api/v1/router.py` — registrar nuevos sub-routers

**Commit.** `feat(api): rpa, jobs and records endpoints with background tasks`

**Riesgos.**
- Sesiones SQLAlchemy dentro de `BackgroundTasks`: las tasks corren fuera del ciclo de la request → **no reutilizar** `db` inyectada, abrir una nueva `async_session()` dentro de la task.
- Race condition si el frontend hace polling antes de que la task haya empezado → el endpoint de detalle siempre responde con lo que hay en DB (nunca bloquea).

**Validación manual al cerrar la fase.**
- `curl -X POST /api/v1/rpa/extract -d '{"fecha_inicial":"2026-01-01","fecha_final":"2026-01-31","limit":5}'` responde `202`
- `GET /api/v1/jobs` lista la ejecución
- 3s después, `GET /api/v1/records?job_id=X` devuelve 2 records fake

---

## Fase 4: Docker base

**Estado:** ⚪ Pendiente

**Objetivo.** `docker compose up --build` levanta los 4 servicios y el flujo de la Fase 3 funciona sin cambios.

**Entregables.**

- `Dockerfile` — Python 3.12 slim, `pip install -r requirements.txt`, user no-root, `CMD uvicorn …`
- `docker-compose.yml` con servicios:
  - `api` (build local)
  - `db` (`postgres:16-alpine` con healthcheck)
  - `selenium` (`selenium/standalone-chrome:latest`, [D01](./DECISIONES_TECNICAS.md#d01--imagen-de-selenium-seleniumstandalone-chromelatest)) con healthcheck y `:7900` expuesto para noVNC
  - `frontend` — placeholder por ahora (levantará en Fase 6)
- Ajuste de `DATABASE_URL` en `.env.example` al host `db:5432`

**Commit.** `feat(docker): compose with api, db and selenium services`

**Riesgos.**
- La API arranca antes de que `db` esté listo → resuelto con `depends_on.condition: service_healthy`.
- En Apple Silicon, `selenium/standalone-chrome:latest` sin tag explícito puede caer en una imagen AMD64 via QEMU → lento. **Pinear versión arm64-compatible** si aplica, o mantener `:latest` pero documentar.
- Volumes de `postgres_data` persisten entre runs: si se cambia el schema hay que `docker compose down -v`.

**Validación manual al cerrar la fase.**
- `docker compose up --build` arranca los 4 servicios sin errores
- `docker compose ps` muestra todos `healthy`
- `GET http://localhost:8000/api/v1/health` responde `200`
- `http://localhost:4444` muestra la consola de Selenium
- `http://localhost:7900` muestra noVNC (password por defecto `secret`)

---

## Fase 5: Bot RPA real

**Estado:** ⚪ Pendiente

**Objetivo.** Reemplazar el stub por el bot Selenium real que cumple el flujo completo: login → navegar → filtros → buscar → extraer. Esta es la fase **más crítica** (25% de la nota).

**Entregables.** Una serie de commits granulares:

- `feat(rpa): webdriver remote factory and base error types`
  - `app/rpa/__init__.py`
  - `app/rpa/driver.py` — `create_driver()` usando `webdriver.Remote` contra `SELENIUM_HUB_URL`
  - `app/rpa/errors.py` — `BotError`, `LoginError`, `NavigationError`, `FilterError`, `ExtractError`
- `feat(rpa): explicit wait helpers`
  - `app/rpa/waits.py` — `wait_table_refreshed`, `wait_options_populated`, etc. ([D15](./DECISIONES_TECNICAS.md#d15--esperas-explícitas--validación-de-cambio-de-tabla))
- `feat(rpa): login step`
  - `app/rpa/steps/__init__.py`, `app/rpa/steps/login.py`
- `feat(rpa): navigate to generar factura`
  - `app/rpa/steps/navigate.py`
- `feat(rpa): apply filters with dependent contrato select`
  - `app/rpa/steps/filters.py`
- `feat(rpa): extract rows with limit`
  - `app/rpa/steps/extract.py`
- `feat(rpa): bot orchestrator with screenshot capture on error`
  - `app/rpa/bot.py` ([D16](./DECISIONES_TECNICAS.md#d16--screenshots-automáticos-en-errores-del-bot))
  - `app/services/rpa_runner.py` — reemplazar stub por `bot.run(params)`

**Riesgos.**
- **Selectores Angular Material inestables** (`mat-select-0`, `mat-input-1`): autogenerados, rompen al tocar el form. Preferir `aria-label`, label text, o XPath semántico.
- **`mat-option`** se monta en `cdk-overlay-container`, fuera del form → buscar en `document.body` tras abrir el dropdown.
- **Combo `Contrato`** dependiente del convenio: pobla async → esperar `len(options) > 0` tras elegir convenio, no solo `presence_of`.
- **Validación de que la tabla cambió**: combinar `staleness_of(first_row)` + desaparición del spinner + `presence_of_all_elements_located(tbody tr)` con contenido no-placeholder.
- **Parseo de fechas**: el portal puede mostrar `DD/MM/YYYY` — preservar string original en `raw_row_json`, parsear a ISO solo si el tiempo lo permite.
- **Logout/sesión**: el bot cierra el driver en `finally` → evitar colgar sesiones.

**Validación manual al cerrar la fase.**
- Un `POST /api/v1/rpa/extract` real con fechas válidas termina en `done` con `records_count > 0`
- La tabla `records` tiene `raw_row_json` poblado
- Un fallo forzado (ej. credenciales inválidas vía `.env`) genera un screenshot en `artifacts/screenshots/`

---

## Fase 6: Frontend

**Estado:** ⚪ Pendiente

**Objetivo.** UI de monitoreo con las 3 pantallas obligatorias y los 3 bonus UX aprobados ([D06](./DECISIONES_TECNICAS.md#d06--bonus-ux-incluidos-desde-el-inicio-en-el-frontend)).

**Entregables.**

- Scaffold Vite: `frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/index.css` (con Tailwind)
- `src/App.tsx` con `BrowserRouter` y rutas
- `src/services/api.ts` — cliente tipado contra `/api/v1`
- `src/hooks/useJobPolling.ts` — hook de polling cada `POLL_INTERVAL_SECONDS`
- `src/types/index.ts` — tipos TS de los schemas de la API
- `src/components/ui/` — `Button`, `Card`, `Input`, `Badge` (con color por estado), `Spinner`, `Table`
- `src/pages/NewExtraction.tsx` — pantalla 1
- `src/pages/Jobs.tsx` — pantalla 2 con auto-refresh
- `src/pages/JobDetail.tsx`
- `src/pages/Records.tsx` — pantalla 3 con filtros por `job_id` y `patient_document`
- `src/pages/RecordDetail.tsx` — con bloque `<pre>` para `raw_row_json`
- `frontend/Dockerfile` — multi-stage Node build → Nginx
- `frontend/nginx.conf.template` — proxy `/api/*` → `http://api:8000`
- `docker-compose.yml` — activar servicio `frontend`

**Commit.** `feat(frontend): monitoring ui with new-extraction, jobs, records pages`

**Riesgos.**
- **CORS en dev local** si se corre `vite` fuera de Docker: configurar `CORSMiddleware` en FastAPI con origins permisivas en debug.
- **Proxy en producción vía Nginx**: asegurar que el path `/api/` no duplica el prefijo cuando se re-escribe.
- **Polling con `useEffect`**: limpiar el intervalo en el `return` para evitar leaks al navegar.

**Validación manual al cerrar la fase.**
- `http://localhost` muestra Pantalla 1
- Submit crea un job y redirige al detalle
- La tabla `/jobs` se refresca sola
- Filtrar records por `job_id` funciona

---

## Fase 7: Tests mínimos

**Estado:** ⚪ Pendiente

**Objetivo.** Cobertura básica que demuestre criterio, no exhaustiva. Agregar dependencias de test a un `requirements-dev.txt`.

**Entregables.**

- `requirements-dev.txt` — `pytest`, `pytest-asyncio`, `httpx`, `aiosqlite` (si se usa SQLite en tests)
- `tests/__init__.py`
- `tests/conftest.py` — fixtures de app, db en memoria, cliente async
- `tests/test_api_smoke.py` — `/health`, `POST /rpa/extract` retorna `202` con stub, listados paginan
- `tests/test_schemas.py` — validación de `ExtractRequest` (fecha_inicial ≤ fecha_final, limit > 0)
- `tests/test_rpa_waits.py` — helper `wait_table_refreshed` con driver mock

**Commit.** `test: smoke tests for api and rpa helpers`

**Riesgos.**
- Los `BackgroundTasks` no se ejecutan bajo `TestClient` sync → usar `httpx.AsyncClient` + `ASGITransport`.
- Testear el bot real en CI requeriría levantar Selenium: **fuera de alcance**. Los tests del bot se limitan a los helpers puros.

---

## Fase 8: README final

**Estado:** ⚪ Pendiente

**Objetivo.** Completar las 11 secciones del README y responder las 7 preguntas del **análisis técnico obligatorio** del enunciado (punto 11 del PDF).

**Entregables.**

- `README.md` — todas las secciones completadas con ejemplos reales
- Capturas (PNG) de las 3 pantallas → `docs/images/screenshots/`
- Enlaces cruzados al resto de `docs/`
- Checklist de verificación en local con 6–8 pasos

**Commit.** `docs: final readme with architecture and technical analysis`

**Riesgos.** Ninguno técnico.

---

## Fase 9: BONUS observabilidad

**Estado:** ⚪ Pendiente

**Objetivo.** Migrar logs a formato JSON estructurado, añadir `request_id` y política de reintentos en pasos del bot.

**Entregables.**

- `app/core/logging.py` — formatter JSON con campos `level`, `logger`, `message`, `request_id`, `job_id`, `step`, `timestamp`
- `app/api/middleware.py` — middleware que inyecta `request_id` por header y context var
- `app/rpa/retry.py` — decorator `@retry(max_attempts=3, backoff=ExponentialBackoff)` aplicable a steps frágiles
- Actualizar `steps/filters.py` y `steps/extract.py` para usar `@retry` en acciones idempotentes (select de dropdown, espera de tabla)

**Commit.** `feat(observability): structured logging and retry policy`

**Riesgos.** Bajo.

---

## Fase 10: BONUS despliegue AWS

**Estado:** ⚪ Pendiente

**Objetivo.** Infraestructura como código en AWS: ECS Fargate, RDS PostgreSQL, ALB, ECR, Secrets Manager.

**Entregables.**

- `terraform/main.tf`, `variables.tf`, `outputs.tf`
- `terraform/vpc.tf` — VPC + 2 subnets públicas + 2 privadas
- `terraform/ecr.tf` — repos para `api` y `frontend`
- `terraform/ecs.tf` — cluster + task definition con 3 containers (api, selenium sidecar, nginx frontend)
- `terraform/rds.tf` — RDS Postgres `t3.micro`
- `terraform/alb.tf` — ALB con target group para `api` y para `frontend`
- `terraform/secrets.tf` — Secrets Manager para `PORTAL_USER/PASSWORD`, `DATABASE_URL`
- `terraform/iam.tf`, `security.tf`
- `terraform/terraform.tfvars.example`
- `scripts/deploy.sh` — helper `aws ecr login && docker push && aws ecs update-service`
- `README.md` — nueva sección **Despliegue en AWS**

**Commit.** `feat(infra): terraform for aws fargate deployment`

**Riesgos.**
- `terraform apply` inicial toma ~12–15 min; ALB + RDS son los cuellos.
- Costo: RDS `t3.micro` ≈ USD 15/mes; Fargate puntual ≈ USD 0.04/hora → apagar cluster cuando no se use.
- Selenium en Fargate con poca RAM crashea Chrome → mínimo `1024 MB` en el sidecar.
- El puerto `:7900` (noVNC) **no** se expone en el ALB — queda privado, accesible solo por SSM/bastion.
