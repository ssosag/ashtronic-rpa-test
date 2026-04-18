"""Unit tests for app.rpa.retry."""
from unittest.mock import patch

import pytest

from app.rpa.retry import retry


class Flaky(Exception):
    pass


class Structural(Exception):
    pass


def test_returns_immediately_on_success():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return "ok"

    result = retry(fn, attempts=3, backoff_seconds=0.01, retry_on=(Flaky,), step="test")
    assert result == "ok"
    assert calls["n"] == 1


def test_retries_then_succeeds():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise Flaky("boom")
        return "ok"

    with patch("time.sleep"):  # skip real sleeps
        result = retry(fn, attempts=3, backoff_seconds=0.01, retry_on=(Flaky,), step="test")
    assert result == "ok"
    assert calls["n"] == 3


def test_raises_after_exhausting_attempts():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise Flaky("always fails")

    with patch("time.sleep"), pytest.raises(Flaky):
        retry(fn, attempts=3, backoff_seconds=0.01, retry_on=(Flaky,), step="test")
    assert calls["n"] == 3


def test_does_not_retry_unlisted_exception():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise Structural("not retryable")

    with pytest.raises(Structural):
        retry(fn, attempts=3, backoff_seconds=0.01, retry_on=(Flaky,), step="test")
    assert calls["n"] == 1


def test_rejects_zero_attempts():
    with pytest.raises(ValueError):
        retry(lambda: None, attempts=0, backoff_seconds=0, retry_on=(Flaky,), step="test")
