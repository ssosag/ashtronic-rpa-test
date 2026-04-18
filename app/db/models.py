from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, DateTime, Date, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)
    fecha_inicial: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_final: Mapped[date] = mapped_column(Date, nullable=False)
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    records: Mapped[list["Record"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Job {self.id} status={self.status}>"


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        Index("ix_records_job_id", "job_id"),
        Index("ix_records_patient_document", "patient_document"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    external_row_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    patient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    patient_document: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    date_service: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sede: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    contrato: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    raw_row_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job: Mapped["Job"] = relationship(back_populates="records")

    def __repr__(self) -> str:
        return f"<Record {self.id} job_id={self.job_id}>"
