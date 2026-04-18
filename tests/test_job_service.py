"""Unit tests for job_service functions against a real in-memory DB."""
from datetime import date

from sqlalchemy import select

from app.db.models import Job
from app.services import job_service


async def test_recover_orphan_jobs_marks_queued_and_running(db_session):
    db_session.add_all(
        [
            Job(status="queued", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5),
            Job(status="running", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5),
            Job(status="done", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5),
            Job(status="error", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5),
        ]
    )
    await db_session.commit()

    recovered = await job_service.recover_orphan_jobs(db_session)
    assert recovered == 2

    rows = (await db_session.execute(select(Job))).scalars().all()
    statuses = sorted(j.status for j in rows)
    assert statuses == ["done", "error", "error", "error"]

    orphaned = [j for j in rows if j.error_message and "orphaned" in j.error_message]
    assert len(orphaned) == 2
    for j in orphaned:
        assert j.finished_at is not None


async def test_recover_orphan_jobs_noop_when_none(db_session):
    db_session.add(
        Job(status="done", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5)
    )
    await db_session.commit()
    recovered = await job_service.recover_orphan_jobs(db_session)
    assert recovered == 0


async def test_list_jobs_orders_by_created_at_desc(db_session):
    j1 = Job(status="done", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5)
    db_session.add(j1)
    await db_session.commit()
    j2 = Job(status="done", fecha_inicial=date(2026, 1, 1), fecha_final=date(2026, 1, 2), limit=5)
    db_session.add(j2)
    await db_session.commit()

    result = await job_service.list_jobs(db_session)
    assert [j.id for j in result] == [j2.id, j1.id]
