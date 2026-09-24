from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import ValidationError
from app.core.security import verify_api_key, check_rate_limit
from app.routing.parsing import sanitize_payload
from app.routing.models import Parcel, format_validation_errors
from app.routing.engine import RoutingEngine
from app.core.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1")

@router.post(
    "/route", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)]
)
async def route_parcel(request: Request):
    logger.info("Received new routing request")
    engine = RoutingEngine()
    
    try:
        raw_payload = await request.json()
    except Exception:
        logger.warning("Rejected request: Invalid JSON format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid JSON format"
        )
    
    try:
        clean_payload = sanitize_payload(raw_payload)
    except ValueError as e:
        logger.warning(f"Rejected request: Payload sanitization failed - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
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