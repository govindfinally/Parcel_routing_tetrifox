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
    except ValueError as e:
        logger.warning(f"Sanitization failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    try:
        engine = RoutingEngine()
        decision = engine.route(parcel)  # <--- FIXED: using .route()
        
        logger.info("Parcel routed successfully", extra={
            "parcel_id": decision.parcel_id,  # <--- FIXED: using dot notation
            "department": decision.department
        })
        
        return decision
    except Exception as e:
        print("!!! ROUTING CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ENGINE CRASH: {str(e)}")

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

    if not isinstance(raw_json, list):
        raise HTTPException(status_code=400, detail="Batch payload must be a JSON array (list)")

    if len(raw_json) > 100:
        raise HTTPException(status_code=413, detail="Batch size exceeds limit of 100 parcels.")

    decisions = []
    errors = []

    try:
        engine = RoutingEngine()
    except Exception as e:
        print("!!! BATCH ENGINE INIT CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ENGINE CRASH: {str(e)}")

    for index, raw_item in enumerate(raw_json):
        try:
            clean_data = sanitize_payload(raw_item)
            parcel = Parcel(**clean_data)
            decision = engine.route(parcel)  # <--- FIXED: using .route()
            decisions.append(decision)
        except (ValidationError, ValueError) as e:
            error_detail = format_validation_errors(e) if isinstance(e, ValidationError) else str(e)
            errors.append({"index": index, "error": error_detail})
        except Exception as e:
            print(f"!!! BATCH ROW {index} CRASHED !!!")
            traceback.print_exc()
            errors.append({"index": index, "error": f"ENGINE CRASH: {str(e)}"})

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
    1 / 0