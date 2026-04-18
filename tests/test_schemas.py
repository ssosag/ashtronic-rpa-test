"""Pydantic schema validation tests for ExtractRequest."""
import pytest
from pydantic import ValidationError

from app.schemas.rpa import ExtractRequest


def test_valid_request():
    req = ExtractRequest(fecha_inicial="2026-01-01", fecha_final="2026-01-31", limit=10)
    assert req.limit == 10


def test_limit_zero_rejected():
    with pytest.raises(ValidationError):
        ExtractRequest(fecha_inicial="2026-01-01", fecha_final="2026-01-31", limit=0)


def test_limit_negative_rejected():
    with pytest.raises(ValidationError):
        ExtractRequest(fecha_inicial="2026-01-01", fecha_final="2026-01-31", limit=-5)


def test_fecha_inicial_after_final_rejected():
    with pytest.raises(ValidationError) as exc:
        ExtractRequest(fecha_inicial="2026-02-01", fecha_final="2026-01-01", limit=10)
    assert "fecha_inicial" in str(exc.value)


def test_same_date_allowed():
    req = ExtractRequest(fecha_inicial="2026-01-01", fecha_final="2026-01-01", limit=1)
    assert req.fecha_inicial == req.fecha_final


def test_invalid_date_format_rejected():
    with pytest.raises(ValidationError):
        ExtractRequest(fecha_inicial="not-a-date", fecha_final="2026-01-31", limit=10)


def test_limit_no_upper_bound():
    req = ExtractRequest(fecha_inicial="2026-01-01", fecha_final="2026-01-31", limit=100000)
    assert req.limit == 100000
