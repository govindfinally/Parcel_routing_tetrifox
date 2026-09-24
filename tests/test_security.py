import time
from collections import defaultdict
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_rate_limit_records = defaultdict(list)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return api_key


async def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    _rate_limit_records[client_ip] = [
        timestamp for timestamp in _rate_limit_records[client_ip]
        if current_time - timestamp < settings.rate_limit_window_seconds
    ]
    
    if len(_rate_limit_records[client_ip]) >= settings.rate_limit_requests:
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    _rate_limit_records[client_ip].append(current_time)


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > settings.max_payload_size_bytes:
            return JSONResponse(
                status_code=413, 
                content={"detail": "Payload Too Large"}
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response