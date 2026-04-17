# Decisiones técnicas

Registro vivo de las decisiones de arquitectura y diseño tomadas durante la construcción de la solución. Cada entrada responde **qué** se decidió y, sobre todo, **por qué**. Este archivo se actualiza fase a fase.

---

## Índice

- [D01 · Imagen de Selenium: `selenium/standalone-chrome:latest`](#d01--imagen-de-selenium-seleniumstandalone-chromelatest)
- [D02 · Base de datos: PostgreSQL 16 con asyncpg](#d02--base-de-datos-postgresql-16-con-asyncpg)
- [D03 · Migraciones: `SQLAlchemy.create_all` en el startup (sin Alembic)](#d03--migraciones-sqlalchemycreate_all-en-el-startup-sin-alembic)
- [D04 · Sin autenticación en la API](#d04--sin-autenticación-en-la-api)
- [D05 · Logging plano en Fase 1, estructurado JSON en Fase 9 (bonus)](#d05--logging-plano-en-fase-1-estructurado-json-en-fase-9-bonus)
- [D06 · Bonus UX incluidos desde el inicio en el frontend](#d06--bonus-ux-incluidos-desde-el-inicio-en-el-frontend)
- [D07 · Solo `requirements.txt` (sin `pyproject.toml`)](#d07--solo-requirementstxt-sin-pyprojecttoml)
- [D08 · Tests en Fase 7, no antes](#d08--tests-en-fase-7-no-antes)
- [D09 · Commit + push tras cada avance significativo](#d09--commit--push-tras-cada-avance-significativo)
- [D10 · Ejecución asíncrona del bot con `BackgroundTasks`](#d10--ejecución-asíncrona-del-bot-con-backgroundtasks)
- [D11 · Selenium en contenedor separado del API](#d11--selenium-en-contenedor-separado-del-api)
- [D12 · API versionada bajo `/api/v1/`](#d12--api-versionada-bajo-apiv1)
- [D13 · Modelos `Job (1) ── (N) Record` con `raw_row_json`](#d13--modelos-job-1--n-record-con-raw_row_json)
- [D14 · Estados del job: `queued → running → done | error`](#d14--estados-del-job-queued--running--done--error)
- [D15 · Esperas explícitas + validación de cambio de tabla](#d15--esperas-explícitas--validación-de-cambio-de-tabla)
- [D16 · Screenshots automáticos en errores del bot](#d16--screenshots-automáticos-en-errores-del-bot)
- [D17 · Conventional Commits](#d17--conventional-commits)

---

## D01 · Imagen de Selenium: `selenium/standalone-chrome:latest`

**Qué:** usamos la imagen oficial `selenium/standalone-chrome:latest` en lugar de montar `selenium-hub` + `node-chrome` separados, y en lugar de instalar Chrome + chromedriver dentro de la imagen del API.

**Por qué:**
- Reduce el tamaño y la complejidad del `Dockerfile` de la API (queda Python puro).
- `standalone-chrome` ya resuelve compatibilidad Chrome ↔ chromedriver, VNC, y configuración para contenedores.
- La modalidad hub + nodes agrega complejidad que no necesitamos (YAGNI): no hay paralelismo de bots en esta prueba.
- El contenedor expone `4444` (WebDriver) y `7900` (noVNC), útil para depurar visualmente con `SE_START_XVFB=true`.

**Consecuencias:**
- El bot usa `webdriver.Remote(command_executor=SELENIUM_HUB_URL)`.
- Debemos esperar a que el contenedor Selenium esté `healthy` antes del arranque de la API.
- En AWS ([Fase 10](./ROADMAP.md#fase-10-bonus-despliegue-aws)), lo más cercano es correr Selenium como sidecar en la misma task definition de ECS.

---

## D02 · Base de datos: PostgreSQL 16 con asyncpg

**Qué:** PostgreSQL 16 como motor. Driver `asyncpg` a través de SQLAlchemy 2.0 async.

**Por qué:**
- El enunciado permite Postgres o MySQL; Postgres tiene mejor soporte para `JSONB` (usado en `raw_row_json` para trazabilidad).
- `asyncpg` es el driver async más maduro, compatible con el event loop de FastAPI.
- Stack probado en el proyecto de referencia del autor, bajo riesgo de integración.

**Consecuencias:**
- `DATABASE_URL` debe usar esquema `postgresql+asyncpg://` (normalizamos en el config si llega como `postgresql://`).
- En migración a RDS ([Fase 10](./ROADMAP.md#fase-10-bonus-despliegue-aws)), el mismo esquema aplica sin cambios en el código.

---

## D03 · Migraciones: `SQLAlchemy.create_all` en el startup (sin Alembic)

**Qué:** el schema se crea automáticamente con `Base.metadata.create_all` en el `lifespan` de FastAPI.

**Por qué:**
- Modelo pequeño (2 tablas): el costo de Alembic no se justifica para la prueba.
- `create_all` hace el arranque reproducible de una máquina limpia con `docker compose up --build` al primer intento (requisito duro del enunciado).
- Alembic sumaría al menos un archivo de config + carpeta de versiones + comandos adicionales en el entrypoint.

**Consecuencias:**
- **No es válido para producción.** En el análisis técnico del README se documenta explícitamente qué cambiaría: adoptar Alembic, `alembic upgrade head` como paso previo al `uvicorn`. En una migración a RDS ([Fase 10](./ROADMAP.md#fase-10-bonus-despliegue-aws)) ese cambio se vuelve prerequisito.
- Un cambio de schema requeriría borrar el volumen `postgres_data` en dev.

---

## D04 · Sin autenticación en la API

**Qué:** la API no pide API key ni JWT para esta entrega.

**Por qué:**
- El enunciado no lo exige.
- Simplifica la integración con el frontend y con las pruebas `curl` del evaluador.
- El frontend y la API corren en la misma red local / dominio, no expuestos a internet en la prueba.

**Consecuencias:**
- Documentar explícitamente en el análisis técnico del README que **para producción habría que sumar API key o JWT + CORS restringido + rate limiting**.

---

## D05 · Logging plano en Fase 1, estructurado JSON en Fase 9 (bonus)

**Qué:** logging con `logging.basicConfig` estándar en las primeras fases. Migrar a formato JSON con `request_id` y contexto por paso del bot en [Fase 9](./ROADMAP.md#fase-9-bonus-observabilidad) como bonus de observabilidad.

**Por qué:**
- El logging plano es suficiente para desarrollo y cumple el requisito obligatorio "logs claros que permitan entender qué paso del flujo se está ejecutando".
- JSON estructurado es un esfuerzo adicional que aporta valor principalmente en agregadores (CloudWatch, ELK) — relevante solo si se despliega en AWS.

**Consecuencias:**
- Los logs de las primeras fases tendrán formato `"%(asctime)s %(levelname)s %(name)s - %(message)s"` con campos como `step=…`, `job_id=…` embebidos en el mensaje para facilitar grep.

---

## D06 · Bonus UX incluidos desde el inicio en el frontend

**Qué:** incluir desde el primer commit del frontend:
- Badges de estado con color por `queued | running | done | error`.
- Auto-refresh de la tabla de Jobs cada `POLL_INTERVAL_SECONDS`.
- Filtros en `/records` por `job_id` y `patient_document`.

**Por qué:**
- El frontend pesa 20% de la nota.
- Estos 3 extras son baratos técnicamente (hook de polling + dos queries) y elevan mucho la percepción de calidad.

**Consecuencias:**
- El hook `useJobPolling` se diseña genérico para reusar.
- `GET /records` debe aceptar `job_id` y `patient_document` como query params desde Fase 3.

---

## D07 · Solo `requirements.txt` (sin `pyproject.toml`)

**Qué:** lista de dependencias en `requirements.txt` con rangos de versión (`paquete>=X,<Y`).

**Por qué:**
- Build de Docker más directo (`pip install -r requirements.txt`).
- El enunciado valora reproducibilidad; rangos compatibles son un balance razonable sin llegar a pinear con hashes.
- `pyproject.toml` aportaría metadatos innecesarios para una app no publicada como paquete.

**Consecuencias:**
- Si aparecen incompatibilidades en el futuro, migrar a `uv` / `poetry` es un paso aislado.

---

## D08 · Tests en Fase 7, no antes

**Qué:** se escriben tests mínimos (smoke de endpoints, validación de schemas, helpers de espera del bot) tras tener el happy path funcionando. Planificación detallada en [Fase 7 del roadmap](./ROADMAP.md#fase-7-tests-mínimos).

**Por qué:**
- TDD estricto triplica el tiempo de una prueba pequeña; el enunciado los marca como **bonus**, no obligatorios.
- Con el happy path estable, los tests que se escriben son más representativos del comportamiento real.

**Consecuencias:**
- Los helpers de espera del bot (`waits.py`) se diseñan desde el inicio como funciones puras con el `driver` inyectado para que sean testeables con mocks en Fase 7.

---

## D09 · Commit + push tras cada avance significativo

**Qué:** cada entregable de fase (o sub-fase) tiene su commit con mensaje Conventional Commits y se hace `git push` inmediato al remote.

**Por qué:**
- El enunciado valora explícitamente "historial de commits legible" (punto 10).
- Permite al evaluador seguir la progresión real del trabajo y no solo ver un dump final.

**Consecuencias:**
- Mayor disciplina en no mezclar cambios de fases distintas en un mismo commit.
- Ningún commit se ejecuta sin aprobación explícita del autor durante esta prueba.

---

## D10 · Ejecución asíncrona del bot con `BackgroundTasks`

**Qué:** el endpoint `POST /api/v1/rpa/extract` responde `202 Accepted` con `{job_id, status: "queued"}` de forma inmediata y el bot corre en segundo plano con `fastapi.BackgroundTasks`.

**Por qué:**
- Una extracción puede tardar decenas de segundos (login + navegación + filtros Angular + N filas). Una ejecución síncrona tendría alto riesgo de timeout HTTP.
- El frontend hace polling, modelo UX simple y claro.
- Evita necesitar Celery / Redis / RQ para una prueba técnica (YAGNI).

**Consecuencias:**
- Limitación real: si la API se reinicia mientras un job está `running`, el job queda "huérfano". **Documentado en el análisis técnico**: en producción se movería a Celery con backend Redis o a SQS.
- Aprovechamos `asyncio.to_thread` para que el código Selenium (sync) no bloquee el event loop.

---

## D11 · Selenium en contenedor separado del API

**Qué:** `selenium` es un servicio de Docker Compose independiente; la API no tiene Chrome ni chromedriver instalados en su imagen.

**Por qué:**
- **Separación de responsabilidades**: la API es Python puro; los detalles del browser están encapsulados en la imagen oficial de Selenium.
- Imagen de la API ~250 MB vs. ~1.5 GB si incluye Chrome.
- Actualizaciones de Chrome (incompatibilidades chromedriver) se resuelven cambiando un solo tag de imagen.
- Permite depurar visualmente vía noVNC sobre `:7900` sin tocar el código de la API.

**Consecuencias:**
- El bot se conecta con `webdriver.Remote(command_executor=…)` en vez de `webdriver.Chrome(...)`.
- Orden de arranque: la API necesita esperar al healthcheck de Selenium.

---

## D12 · API versionada bajo `/api/v1/`

**Qué:** todos los endpoints cuelgan de `/api/v1/*`.

**Por qué:**
- Permite introducir `/api/v2/` sin romper consumidores existentes.
- Convención clara para el frontend (`API_BASE = "/api/v1"`).

**Consecuencias:**
- Nginx del frontend proxy-pasa `/api/*` al servicio `api`.

---

## D13 · Modelos `Job (1) ── (N) Record` con `raw_row_json`

**Qué:** dos tablas con relación 1:N. `Record` guarda tanto columnas normalizadas (`patient_name`, `patient_document`, …) como `raw_row_json` (JSONB) con todo lo extraído de la fila.

**Por qué:**
- Los campos normalizados cubren las consultas frecuentes y filtros del frontend.
- `raw_row_json` garantiza **trazabilidad total**: si el portal muestra una columna no contemplada en el modelo, queda registrada sin pérdida.
- Es un patrón común en ingesta: "capture raw, normalize on read".

**Consecuencias:**
- `raw_row_json` se renderiza en la vista de detalle del record del frontend como bloque `<pre>`.

---

## D14 · Estados del job: `queued → running → done | error`

**Qué:** 4 estados discretos, modelados como enum en Pydantic y como `VARCHAR` + check constraint en Postgres (opcional).

**Por qué:**
- Refleja el ciclo de vida real.
- Los estados son terminales (`done`, `error`) o no-terminales (`queued`, `running`) — el frontend detiene el polling al alcanzar un estado terminal.

**Consecuencias:**
- `finished_at` y `error_message` solo se setean en la transición a estado terminal.

---

## D15 · Esperas explícitas + validación de cambio de tabla

**Qué:** ninguna parte del bot usa `time.sleep(n)` como mecanismo principal. Todas las esperas son:
- `WebDriverWait(driver, T).until(EC.presence_of_element_located(...))` o similares.
- Para "esperar que la tabla cambió tras click en Buscar": combinación de:
  1. `staleness_of(primera_fila_snapshot)` tomada ANTES del click.
  2. Desaparición del spinner (`invisibility_of_element_located`).
  3. Presencia de nuevas filas con contenido distinto o explícito check del placeholder "cargando".

**Por qué:**
- Es un requisito obligatorio y explícito del enunciado.
- `time.sleep` es frágil: demasiado corto → flaky; demasiado largo → lento.

**Consecuencias:**
- Helper `wait_table_refreshed(driver, snapshot)` en `app/rpa/waits.py`, testeable en [Fase 7](./ROADMAP.md#fase-7-tests-mínimos) con mocks.

---

## D16 · Screenshots automáticos en errores del bot

**Qué:** cualquier excepción dentro de un `step` del bot dispara `driver.save_screenshot(path)` antes de propagar.

**Por qué:**
- Trazabilidad post-mortem: permite ver el estado del DOM en el momento del fallo sin reproducir.
- Es una mejor práctica que el enunciado valora implícitamente en "robustez y trazabilidad".

**Consecuencias:**
- Carpeta `artifacts/screenshots/` gitignoreada con `.gitkeep` para preservar la ruta.
- El nombre del archivo incluye `job_id`, `step`, y timestamp UTC: `job_{id}_{step}_{ts}.png`.

---

## D17 · Conventional Commits

**Qué:** todos los commits siguen el formato `<tipo>(<scope>): <mensaje>` — tipos `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.

**Por qué:**
- Historial legible (requisito del enunciado).
- Facilita generar un changelog automático si se quisiera.

**Consecuencias:**
- Ejemplos: `feat(rpa): apply savia salud filter with explicit waits`, `docs: technical analysis section in readme`.
