from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from pydantic import ValidationError

from app.core.security import verify_api_key, check_rate_limit
from app.routing.parsing import sanitize_payload
from app.routing.models import Parcel, format_validation_errors
from app.routing.engine import RoutingEngine
from app.core.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter()
engine = RoutingEngine("config/rules.yaml")

@router.post("/route", dependencies=[Depends(check_rate_limit)])
async def route_parcel(
    request: Request,
    api_key_user: str = Depends(verify_api_key)
):
    """
    Process a single parcel routing request.
    """
    # 1. Read Raw JSON (To prevent Pydantic from crashing on malicious payloads)
    try:
        raw_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    # 2. Sanitize and Validate
    try:
        clean_data = sanitize_payload(raw_json)
        parcel = Parcel(**clean_data)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e.errors()}")
        raise HTTPException(
            status_code=422, 
            detail=format_validation_errors(e)
        )
    except ValueError as e:
        logger.warning(f"Sanitization failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Evaluate Rules
    decision = engine.evaluate(parcel)
    
    # 4. Log and Return
    logger.info("Parcel routed successfully", extra={
        "parcel_id": decision["parcel_id"],
        "department": decision["department"]
    })
    
    return decision

@router.post("/route/batch", dependencies=[Depends(check_rate_limit)])
async def route_parcel_batch(
    request: Request,
    api_key_user: str = Depends(verify_api_key)
):
    """
    Process a batch of parcels. Limits batch size to 100 to prevent blocking.
    """
    try:
        raw_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    # Ensure payload is a list
    if not isinstance(raw_json, list):
        raise HTTPException(status_code=400, detail="Batch payload must be a JSON array (list)")

    # Enforce batch size limit
    if len(raw_json) > 100:
        raise HTTPException(status_code=413, detail="Batch size exceeds limit of 100 parcels.")

    decisions = []
    errors = []

    # Process each parcel in the batch
    for index, raw_item in enumerate(raw_json):
        try:
            clean_data = sanitize_payload(raw_item)
            parcel = Parcel(**clean_data)
            decision = engine.evaluate(parcel)
            decisions.append(decision)
        except (ValidationError, ValueError) as e:
            # If one fails, record the error but don't crash the whole batch
            error_detail = format_validation_errors(e) if isinstance(e, ValidationError) else str(e)
            errors.append({"index": index, "error": error_detail})

    logger.info("Batch processed", extra={
        "total_processed": len(decisions),
        "total_failed": len(errors)
    })

    return {
        "status": "completed",
        "processed_count": len(decisions),
        "failed_count": len(errors),
        "results": decisions,
        "errors": errors
    }

@router.post("/force-error", dependencies=[Depends(check_rate_limit)])
async def force_error(api_key_user: str = Depends(verify_api_key)):
    """
    Simulates a critical system failure to test the global exception handler.
    """
    logger.error("Simulating system crash!")
    # Trigger a division by zero to crash the app safely
    1 / 0