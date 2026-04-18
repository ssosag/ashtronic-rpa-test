"""ASGI middleware that assigns a request_id to each request and echoes it back.

- Reads `X-Request-ID` from the incoming request; generates a UUID4 if absent.
- Stores it in `request_id_var` (ContextVar) so any log emitted during the request
  carries it automatically via `JsonFormatter`.
- Echoes the id back in the `X-Request-ID` response header so clients can correlate.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["x-request-id"] = rid
        return response
