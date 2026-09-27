from typing import List, Dict, Any
import traceback
from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from pydantic import ValidationError

from app.core.security import verify_api_key, check_rate_limit
from app.routing.parsing import sanitize_payload
from app.routing.models import Parcel, format_validation_errors
from app.routing.engine import RoutingEngine
from app.core.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.post("/route", dependencies=[Depends(check_rate_limit)])
async def route_parcel(
    request: Request,
    api_key_user: str = Depends(verify_api_key)
):
    """
    Process a single parcel routing request.
    """
    try:
        raw_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    try:
        clean_data = sanitize_payload(raw_json)
        parcel = Parcel(**clean_data)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e.errors()}")
        raise HTTPException(
            status_code=422, 
            detail=format_validation_errors(e)
        )
        
    try:
        parcel = Parcel(**clean_payload)
    except ValidationError as exc:
        errors = format_validation_errors(exc)
        logger.warning(f"Rejected request: Pydantic validation failed - {errors}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"errors": errors}
        )
        
    decision = engine.route(parcel)
    logger.info(f"Successfully processed routing for parcel [{decision.parcel_id}]")
    return decision

@router.post("/force-error", dependencies=[Depends(verify_api_key)])
async def force_error_endpoint():
    # This email will be automatically redacted in the logs
    logger.info("User with email test.user@example.com is attempting a forced crash.")
    
    # Intentionally cause a crash to trigger the global exception handler
    bad_math = 1 / 0 
    
    return {"message": "You will never see this."}