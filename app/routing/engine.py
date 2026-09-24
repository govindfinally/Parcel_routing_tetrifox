import uuid
from typing import Dict, Any
from app.routing.models import Parcel, Decision
from app.routing.rules_config import RulesConfig
from app.core.logging import setup_logger

logger = setup_logger(__name__)

class RoutingEngine:
    def __init__(self):
        self.rules = RulesConfig.get_rules()

    def route(self, parcel: Parcel) -> Decision:
        context: Dict[str, Any] = {
            "weight": float(parcel.weight),
            "value": float(parcel.value),
            "country": parcel.country,
        }
        
        if parcel.attributes:
            context.update(parcel.attributes)

        matched_rule = "default_fallback"
        department = "Manual Review"
        parcel_id = parcel.id or f"pkg-{uuid.uuid4().hex[:8]}"

        for rule in self.rules:
            try:
                if eval(rule.condition, {"__builtins__": {}}, context):
                    matched_rule = rule.name
                    department = rule.department
                    logger.info(f"Parcel [{parcel_id}] matched rule: '{rule.name}' -> Routed to {department}")
                    break
            except Exception as e:
                logger.warning(f"Rule evaluation skipped for '{rule.name}': {str(e)}")
                continue

        if matched_rule == "default_fallback":
            logger.info(f"Parcel [{parcel_id}] matched NO rules. Routed to {department} (Fallback)")

        return Decision(
            parcel_id=parcel_id,
            weight_kg=str(parcel.weight),
            value_eur=str(parcel.value),
            department=department,
            status="ROUTED",
            approvals_required=[],
            matched_rule=matched_rule,
            gates_triggered=[],
            reason=f"Matched rule: {matched_rule}",
            ruleset_version="1.0"
        )