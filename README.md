# Ashtronic RPA Test — Prueba técnica Santiago Sosa

> Solución end-to-end RPA + Backend + Base de datos + Frontend de monitoreo para extraer registros de facturación del portal Hiruko Prodiagnóstico.

**Estado:** 🚧 en construcción (Fase 0 — Bootstrap).

---

## 1. Descripción general

_Pendiente: resumen del sistema al terminar cada fase._

## 2. Arquitectura propuesta

El sistema se compone de 4 servicios orquestados con Docker Compose:

- **frontend** — React + Vite servido con Nginx
- **api** — FastAPI con ejecución asíncrona del bot vía `BackgroundTasks`
- **db** — PostgreSQL 16
- **selenium** — `selenium/standalone-chrome:latest` con Chrome headless

Ver diagrama en [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) (diagramas en `docs/images/`).

## 3. Estructura de carpetas

_Pendiente: árbol final al terminar Fase 5._

## 4. Prerrequisitos

- Docker + Docker Compose
- Git

## 5. Variables de entorno

Copiar `.env.example` a `.env` y completar los valores. Variables principales:

| Variable | Propósito |
|---|---|
| `PORTAL_URL` | URL base del portal Hiruko |
| `PORTAL_USER` / `PORTAL_PASSWORD` | Credenciales del portal |
| `DATABASE_URL` | Conexión asyncpg a Postgres |
| `SELENIUM_HUB_URL` | Endpoint del WebDriver remoto |
| `SELENIUM_TIMEOUT` | Timeout global de esperas explícitas (segundos) |
| `SCREENSHOTS_DIR` | Carpeta donde el bot guarda snapshots en error |
| `LOG_LEVEL` | Nivel de logging (`INFO`, `DEBUG`, …) |
| `POLL_INTERVAL_SECONDS` | Intervalo de polling del frontend al estado de un job |

## 6. Cómo levantar la solución

```bash
cp .env.example .env
# editar .env con las credenciales reales
docker compose up --build
```

URLs:

| Servicio | URL |
|---|---|
| Frontend | http://localhost |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Selenium console | http://localhost:4444 |

## 7. Cómo probar los endpoints

_Pendiente: ejemplos `curl` tras Fase 3._

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/rpa/extract` | Dispara una extracción |
| `GET`  | `/api/v1/jobs` | Lista ejecuciones |
| `GET`  | `/api/v1/jobs/{id}` | Detalle de una ejecución |
| `GET`  | `/api/v1/records` | Lista registros extraídos (filtros: `job_id`, `patient_document`) |
| `GET`  | `/api/v1/records/{id}` | Detalle de un registro |

## 8. Cómo usar el frontend

_Pendiente: captura de las 3 pantallas tras Fase 6._

## 9. Flujo general del sistema

1. Usuario abre **Nueva extracción** en el frontend y envía `fecha_inicial`, `fecha_final`, `limit`.
2. El frontend hace `POST /api/v1/rpa/extract`. La API crea un `Job` en estado `queued`, encola una `BackgroundTask` y responde `202` con `job_id`.
3. La `BackgroundTask` marca el job como `running`, abre un WebDriver remoto contra el contenedor Selenium y ejecuta los pasos: `login → navigate → filters → extract`.
4. Cada fila extraída se persiste como `Record` asociado al `Job`. Al terminar, el job pasa a `done`. Si algo falla, pasa a `error` con `error_message` y se guarda un screenshot.
5. El frontend consulta `GET /api/v1/jobs/{id}` cada `POLL_INTERVAL_SECONDS` hasta que el estado sea terminal.

## 10. Checklist de verificación en local

- [ ] `cp .env.example .env` y completar credenciales
- [ ] `docker compose up --build` arranca sin errores
- [ ] `http://localhost:8000/api/v1/health` responde `200`
- [ ] `http://localhost:4444` muestra la consola de Selenium
- [ ] `http://localhost` carga el frontend
- [ ] Una extracción de prueba termina en estado `done`

## 11. Análisis técnico

> Respuestas a las 7 preguntas obligatorias del enunciado. _Pendientes hasta [Fase 8](./docs/ROADMAP.md#fase-8-readme-final)._

1. **¿Por qué esta arquitectura?** _TODO_
2. **Ventajas de la propuesta.** _TODO_
3. **Desventajas, límites o riesgos.** _TODO_
4. **Decisiones por simplicidad o tiempo.** _TODO_
5. **Qué mejoraría con más tiempo.** _TODO_
6. **Cómo escalaría si el volumen creciera.** _TODO_
7. **Qué faltaría para llevar a producción.** _TODO_
8. **Evolución futura.** _TODO_

## 12. Estado del proyecto

Plan de construcción completo en [`docs/ROADMAP.md`](./docs/ROADMAP.md).

| Fase | Estado |
|---|---|
| 0 — Bootstrap | 🟡 En curso |
| 1 — Backend skeleton | ⚪ Pendiente |
| 2 — DB y modelos | ⚪ Pendiente |
| 3 — Endpoints (stub) | ⚪ Pendiente |
| 4 — Docker base | ⚪ Pendiente |
| 5 — Bot RPA real | ⚪ Pendiente |
| 6 — Frontend | ⚪ Pendiente |
| 7 — Tests mínimos | ⚪ Pendiente |
| 8 — README final | ⚪ Pendiente |
| 9 — BONUS observabilidad | ⚪ Pendiente |
| 10 — BONUS despliegue AWS | ⚪ Pendiente |

---

## Documentación complementaria

- [`docs/ROADMAP.md`](./docs/ROADMAP.md) — plan de construcción fase a fase con entregables, commits y riesgos.
- [`docs/DECISIONES_TECNICAS.md`](./docs/DECISIONES_TECNICAS.md) — registro vivo de decisiones con su justificación.
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — diagramas (ERD, arquitectura, flujo del bot, secuencia, wireframes).
