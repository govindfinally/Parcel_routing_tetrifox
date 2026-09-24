import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request

from app.core.security import SecurityHeadersMiddleware, PayloadSizeLimitMiddleware
from app.api.routes import router as api_router
from app.routing.rules_config import RulesConfig
from app.core.logging import setup_logger, request_id_ctx_var
from app.core.errors import global_exception_handler
from app.core.monitoring import monitor

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        RulesConfig.load("config/rules.yaml")
        logger.info("Rules loaded successfully on startup.")
    except Exception as e:
        logger.error(f"Failed to load rules on startup: {e}")
    yield
    logger.info("Server shutting down.")

app = FastAPI(title="Secure Parcel Routing Engine", lifespan=lifespan)

# Register the global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# 1. Request ID Generation Middleware (Runs first)
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_ctx_var.set(req_id)
    monitor.record_request()
    
    response = await call_next(request)
    
    # Return the ID in the header so the client can quote it for support
    response.headers["X-Request-ID"] = req_id
    return response

# 2. Security Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PayloadSizeLimitMiddleware)

app.include_router(api_router)