from typing import List, Dict, Any
import traceback
from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from pydantic import ValidationError

from app.core.security import verify_api_key, check_rate_limit, verify_dev_api_key
from app.routing.parsing import sanitize_payload
from app.routing.models import Parcel, format_validation_errors
from app.routing.engine import RoutingEngine
from app.core.logging import setup_logger
from app.routing.rules_config import RulesConfig
import yaml
import os
from app.routing.rules_loader import load_rules, RuleLoaderError

RULES_FILE = "config/rules.yaml"

logger = setup_logger(__name__)
router = APIRouter()
def get_Routing_engine():
    return RoutingEngine()
@router.post("/route", dependencies=[Depends(check_rate_limit)])

async def route_parcel(
    request: Request,
    api_key_user: str = Depends(verify_api_key),
    engine:RoutingEngine=Depends(get_Routing_engine)
):
    """
    Process a single parcel routing request.
    """
    try:
        raw_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    try:
        
        clean_payload = sanitize_payload(raw_json)
        parcel = Parcel(**clean_payload)
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
    try:
        decision = engine.route(parcel)
        logger.info(f"Successfully processed routing for parcel [{decision.parcel_id}]")
        return decision
    except HTTPException as e:
        print(e)
        

@router.post("/force-error", dependencies=[Depends(verify_api_key)])
async def force_error_endpoint():
    # This email will be automatically redacted in the logs
    logger.info("User with email test.user@example.com is attempting a forced crash.")
    
    # Intentionally cause a crash to trigger the global exception handler
    bad_math = 1 / 0 
    
    return {"message": "You will never see this."}
@router.get("/admin/rules", dependencies=[Depends(verify_dev_api_key)])
async def get_routing_rules(engine: RoutingEngine = Depends(get_Routing_engine)):
    """
    Retrieve the current routing rules.
    """
    try:
        rules = RulesConfig.get_rules()
        return [{"name": r.name, "priority": r.priority, "condition": r.condition, "department": r.department} for r in rules]
    except Exception as e:
        logger.error(f"Failed to retrieve routing rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/admin/rules", dependencies=[Depends(check_rate_limit)])
async def upsert_rule(new_rule: dict, dev_key: str = Depends(verify_dev_api_key)):
    """
    PM ek naya rule bhejta hai: {"name": ..., "priority": ..., "condition": ..., "department": ...}
    Agar wahi naam ka rule already hai, update hota hai; nahi toh add hota hai.
    """
    with open(RULES_FILE, "r") as f:
        data = yaml.safe_load(f)

    existing = [r for r in data["rules"] if r["name"] != new_rule["name"]]
    existing.append(new_rule)
    data["rules"] = existing

    temp_path = RULES_FILE + ".tmp"
    with open(temp_path, "w") as f:
        yaml.safe_dump(data, f)

    try:
        load_rules(temp_path)   # validate BEFORE touching real file
    except RuleLoaderError as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Invalid rule: {str(e)}")

    os.replace(temp_path, RULES_FILE)   # atomic swap, real file safe tak invalid nahi hota
    RulesConfig.load(RULES_FILE)         # in-memory cache refresh

    return {"status": "success", "message": f"Rule '{new_rule['name']}' saved and reloaded."}
@router.delete("/admin/rules/{rule_name}", dependencies=[Depends(check_rate_limit)])
async def delete_rule(rule_name: str, dev_key: str = Depends(verify_dev_api_key)):
    """
    PM diye gaye naam ka rule delete karta hai rules.yaml se.
    """
    with open(RULES_FILE, "r") as f:
        data = yaml.safe_load(f)

    original_count = len(data["rules"])
    data["rules"] = [r for r in data["rules"] if r["name"] != rule_name]

    if len(data["rules"]) == original_count:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")

    temp_path = RULES_FILE + ".tmp"
    with open(temp_path, "w") as f:
        yaml.safe_dump(data, f)

    try:
        load_rules(temp_path)
    except RuleLoaderError as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Resulting config invalid: {str(e)}")

    os.replace(temp_path, RULES_FILE)
    RulesConfig.load(RULES_FILE)

    return {"status": "success", "message": f"Rule '{rule_name}' deleted and reloaded."}