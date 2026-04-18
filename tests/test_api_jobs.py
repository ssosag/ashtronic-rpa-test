"""Integration tests for /jobs endpoints."""
from datetime import date

from app.db.models import Job


async def test_get_job_404(client):
    resp = await client.get("/api/v1/jobs/9999")
    assert resp.status_code == 404


async def test_list_jobs_empty(client):
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_jobs_returns_created(client, db_session):
    job = Job(
        status="done",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 31),
        limit=10,
        records_count=3,
    )
    db_session.add(job)
    await db_session.commit()

    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "done"
    assert body[0]["records_count"] == 3


async def test_list_jobs_respects_limit(client, db_session):
    for _ in range(3):
        db_session.add(
            Job(
                status="queued",
                fecha_inicial=date(2026, 1, 1),
                fecha_final=date(2026, 1, 2),
                limit=5,
            )
        )
    await db_session.commit()

    resp = await client.get("/api/v1/jobs?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_job_detail(client, db_session):
    job = Job(
        status="running",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 2),
        limit=5,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    resp = await client.get(f"/api/v1/jobs/{job.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job.id
    assert resp.json()["status"] == "running"
