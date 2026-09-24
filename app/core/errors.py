from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import setup_logger, request_id_ctx_var
from app.core.monitoring import monitor

logger = setup_logger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    # 1. Record the metric failure
    monitor.record_error()
    
    # 2. Log the actual technical failure with stack trace internally
    logger.error(f"System crash on path {request.url.path}: {str(exc)}", exc_info=True)
    
    # 3. Return a sterile, safe response to the user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "request_id": request_id_ctx_var.get(),
            "support_code": "ERR-500"
        }
    )