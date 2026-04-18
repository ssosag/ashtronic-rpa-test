# Operación — Comandos útiles

Guía de referencia rápida para operar el proyecto (levantar, ver logs, inspeccionar la DB, verificar reintentos). Los ejemplos están en **PowerShell** (Windows) y **bash** (Linux/Mac) donde la sintaxis cambia.

---

## 1. Ciclo de vida de los contenedores

```bash
docker compose up -d --build        # levantar (o reconstruir) todo
docker compose ps                   # ver estado de los servicios
docker compose restart api          # reiniciar solo la API
docker compose down                 # detener (conserva datos)
docker compose down -v              # detener y BORRAR volúmenes (¡borra la DB!)
```

> Si agregas columnas al modelo (p. ej. `retries_count`), necesitas `down -v` y `up -d` porque `Base.metadata.create_all` **no** altera tablas existentes.

---

## 2. Logs

```bash
docker compose logs -f api          # stream de la API
docker compose logs -f selenium     # stream de Selenium
docker compose logs --tail=200 api  # últimas 200 líneas
```

### Filtrar por patrón

**PowerShell** (no tiene `grep`):

```powershell
docker compose logs -f api | Select-String "retry="
docker compose logs -f api | Select-String "step=extract|step=login"
docker compose logs --tail=500 api | Select-String "job_id=42"
```

Alias corto: `sls`.

**bash**:

```bash
docker compose logs -f api | grep "retry="
docker compose logs -f api | grep -E "step=(extract|login)"
```

### Patrones útiles

| Quiero ver…                       | Patrón                       |
|-----------------------------------|------------------------------|
| Reintentos transitorios           | `retry=transient`            |
| Reintentos agotados (falló)       | `retry=exhausted`            |
| Inicio/fin de un job específico   | `job_id=42`                  |
| Overlay bloqueando el click       | `wait_overlay`               |
| Errores del bot                   | `step=.* error=`             |
| Todo el request_id de una llamada | `request_id=<uuid>`          |

---

## 3. Verificar que los reintentos funcionaron

Después de una extracción con rango grande:

```powershell
docker compose logs --tail=500 api | Select-String "retry="
```

- **Sin líneas** → salió al primer intento (caso normal).
- `retry=transient step=extract attempt=1/3 ...` → reintentó con backoff, todavía puede ganar.
- `retry=exhausted step=extract attempts=3 ...` → agotó los 3 intentos → job queda en `error`.

El frontend también lo muestra: columna **Reintentos** en `/jobs` y campo **Reintentos** en la vista de detalle — badge ámbar cuando `retries_count > 0`.

---

## 4. Base de datos (PostgreSQL)

```bash
docker compose exec db psql -U ashtronic -d ashtronic_rpa
```

Consultas rápidas dentro de `psql`:

```sql
-- últimos jobs
SELECT id, status, records_count, retries_count, error_message, created_at
FROM jobs ORDER BY created_at DESC LIMIT 20;

-- jobs con reintentos
SELECT id, status, retries_count, error_message
FROM jobs WHERE retries_count > 0 ORDER BY created_at DESC;

-- registros de un job
SELECT id, patient_name, patient_document, sede FROM records WHERE job_id = 42;

-- salir
\q
```

---

## 5. Screenshots de errores

El bot guarda un PNG en `./artifacts/screenshots/` cuando falla:

```powershell
Get-ChildItem .\artifacts\screenshots\ | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

```bash
ls -lt artifacts/screenshots/ | head
```

Nombre: `job_<id>_<step>_<timestamp>.png`.

---

## 6. Selenium — depurar visualmente

Abrir `http://localhost:7900` en el navegador (contraseña: `secret`) para ver el Chrome dentro del contenedor en vivo mientras corre el bot.

---

## 7. Tests

```bash
# backend
pytest -q
pytest tests/test_retry.py -v

# frontend
cd frontend
npm test
npm run lint
npm run format:check
```

---

## 8. API — llamadas rápidas con curl

**PowerShell** usa comillas invertidas y JSON con comillas simples:

```powershell
curl -X POST http://localhost:8000/api/v1/rpa/extract `
  -H 'Content-Type: application/json' `
  -d '{"fecha_inicial":"2026-01-01","fecha_final":"2026-01-31","limit":50}'

curl http://localhost:8000/api/v1/jobs/1
curl 'http://localhost:8000/api/v1/records?job_id=1&limit=10'
```
