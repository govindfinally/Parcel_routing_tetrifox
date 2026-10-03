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
            "fragile": getattr(parcel, 'fragile', False),
            
        }
        
        if parcel.attributes:
            context.update(parcel.attributes)

        matching_rules = []
        parcel_id = parcel.id or f"pkg-{uuid.uuid4().hex[:8]}"

        for rule in self.rules:
            try:
                if eval(rule.condition, {"__builtins__": {}}, context):
                    # Tuple mein store kiya: (department, rule name, priority)
                    matching_rules.append((rule.department, rule.name, rule.priority))
                    # Bug 1 Fixed: Pura logger statement likha
                    logger.info(f"Parcel [{parcel_id}] matched rule: '{rule.name}'")
            except Exception as e:
                logger.warning(f"Rule evaluation skipped for '{rule.name}': {str(e)}")
                continue

        # Default fallbacks agar koi rule match na ho
        final_department = "Manual Review"
        final_matched_rule = "default_fallback"

        if matching_rules:
            # Bug 3 Fixed: x[0] ka matlab department ke naam se alphabetical sort. 
            best_match = sorted(matching_rules, key=lambda x: x[0])[0]
            
            # Bug 2 Fixed: Sorted list se data nikal kar variables update kiye
            final_department = best_match[0]
            final_matched_rule = best_match[1]

        # Ab Decision object update hue final variables ko return karega
        return Decision(
            parcel_id=parcel_id,
            weight_kg=str(parcel.weight),
            value_eur=str(parcel.value),
            department=final_department,
            status="ROUTED",
            approvals_required=[],
            matched_rule=final_matched_rule,
            gates_triggered=[],
            reason=f"Matched rule: {final_matched_rule}",
            ruleset_version="1.0"
        )