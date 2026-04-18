"""Integration tests for /records endpoints + filters."""
from datetime import date

from app.db.models import Job, Record


async def _seed(db_session) -> int:
    job = Job(
        status="done",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 31),
        limit=10,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    rows = [
        {"patient_name": "Ana Pérez", "patient_document": "111", "sede": "Bogotá"},
        {"patient_name": "Juan Pérez", "patient_document": "222", "sede": "Bogotá"},
        {"patient_name": "Luis Gómez", "patient_document": "333", "sede": "Medellín"},
    ]
    for r in rows:
        db_session.add(
            Record(
                job_id=job.id,
                patient_name=r["patient_name"],
                patient_document=r["patient_document"],
                sede=r["sede"],
                raw_row_json={},
            )
        )
    await db_session.commit()
    return job.id


async def test_list_records_all(client, db_session):
    await _seed(db_session)
    resp = await client.get("/api/v1/records")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_filter_by_job_id(client, db_session):
    job_id = await _seed(db_session)
    resp = await client.get(f"/api/v1/records?job_id={job_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_filter_by_patient_name(client, db_session):
    await _seed(db_session)
    resp = await client.get("/api/v1/records?patient_name=pérez")
    assert resp.status_code == 200
    names = {r["patient_name"] for r in resp.json()}
    assert names == {"Ana Pérez", "Juan Pérez"}


async def test_filter_by_document(client, db_session):
    await _seed(db_session)
    resp = await client.get("/api/v1/records?patient_document=222")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["patient_document"] == "222"


async def test_filter_by_sede(client, db_session):
    await _seed(db_session)
    resp = await client.get("/api/v1/records?sede=medellín")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["sede"] == "Medellín"


async def test_get_record_404(client):
    resp = await client.get("/api/v1/records/9999")
    assert resp.status_code == 404


async def test_limit_capped_at_500(client):
    resp = await client.get("/api/v1/records?limit=9999")
    assert resp.status_code == 422
