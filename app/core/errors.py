from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import setup_logger, request_id_ctx_var
from app.core.monitoring import monitor

logger = setup_logger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    monitor.record_error()
    logger.error(f"System crash on path {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "request_id": request_id_ctx_var.get(),
            "support_code": "ERR-500"
        }
    )