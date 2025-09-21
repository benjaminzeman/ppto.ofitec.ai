import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration = (time.time() - start) * 1000
            log = {
                "method": request.method,
                "path": request.url.path,
                "status": getattr(response, 'status_code', 'n/a'),
                "duration_ms": round(duration, 2),
            }
            print(json.dumps(log))
