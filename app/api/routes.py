from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import ValidationError
from app.core.security import verify_api_key, check_rate_limit
from app.routing.parsing import sanitize_payload
from app.routing.models import Parcel, format_validation_errors
from app.routing.engine import RoutingEngine

router = APIRouter(prefix="/api/v1")

@router.post(
    "/route", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)]
)
async def route_parcel(request: Request):
    # Initialize Engine HERE, after the server has fully started and rules are loaded
    engine = RoutingEngine()
    
    try:
        raw_payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid JSON format"
        )
    
    try:
        clean_payload = sanitize_payload(raw_payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
        
    try:
        parcel = Parcel(**clean_payload)
    except ValidationError as exc:
        errors = format_validation_errors(exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"errors": errors}
        )
        
    try:
        decision = engine.route(parcel)
        return decision
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during routing"
        )