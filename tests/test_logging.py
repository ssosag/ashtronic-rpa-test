"""Tests for JSON logging + request_id propagation."""
import json
import logging

from app.core.logging import JsonFormatter, request_id_var


def test_json_formatter_basic_fields():
    record = logging.LogRecord(
        name="app.test", level=logging.INFO, pathname="", lineno=0,
        msg="hello", args=None, exc_info=None,
    )
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["msg"] == "hello"
    assert "ts" in payload
    assert "request_id" not in payload  # unset ContextVar


def test_json_formatter_includes_request_id():
    token = request_id_var.set("abc123")
    try:
        record = logging.LogRecord(
            name="app.test", level=logging.INFO, pathname="", lineno=0,
            msg="with-rid", args=None, exc_info=None,
        )
        payload = json.loads(JsonFormatter().format(record))
        assert payload["request_id"] == "abc123"
    finally:
        request_id_var.reset(token)


async def test_middleware_generates_request_id(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) >= 16


async def test_middleware_echoes_incoming_request_id(client):
    resp = await client.get("/api/v1/health", headers={"X-Request-ID": "custom-id-123"})
    assert resp.headers["x-request-id"] == "custom-id-123"
