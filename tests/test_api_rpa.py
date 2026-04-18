"""Integration tests for POST /rpa/extract."""
import pytest

from app.services import rpa_runner


@pytest.fixture(autouse=True)
def _stub_runner(monkeypatch):
    """Replace the real runner with a no-op so tests don't touch Selenium."""
    async def _noop(job_id: int) -> None:
        return None

    monkeypatch.setattr(rpa_runner, "run", _noop)


async def test_extract_returns_202_and_job_id(client):
    resp = await client.post(
        "/api/v1/rpa/extract",
        json={"fecha_inicial": "2026-01-01", "fecha_final": "2026-01-31", "limit": 5},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert isinstance(body["job_id"], int)
    assert body["job_id"] > 0


async def test_extract_rejects_limit_zero(client):
    resp = await client.post(
        "/api/v1/rpa/extract",
        json={"fecha_inicial": "2026-01-01", "fecha_final": "2026-01-31", "limit": 0},
    )
    assert resp.status_code == 422


async def test_extract_rejects_reversed_dates(client):
    resp = await client.post(
        "/api/v1/rpa/extract",
        json={"fecha_inicial": "2026-02-01", "fecha_final": "2026-01-01", "limit": 10},
    )
    assert resp.status_code == 422


async def test_extract_persists_job(client):
    resp = await client.post(
        "/api/v1/rpa/extract",
        json={"fecha_inicial": "2026-01-01", "fecha_final": "2026-01-31", "limit": 5},
    )
    job_id = resp.json()["job_id"]

    detail = await client.get(f"/api/v1/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "queued"
