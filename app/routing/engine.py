import uuid
from typing import Dict, Any
from app.routing.models import Parcel, Decision
from app.routing.rules_config import RulesConfig

class RoutingEngine:
    def __init__(self):
        # Load the rules from memory that were cached when the app started
        self.rules = RulesConfig.get_rules()

    def route(self, parcel: Parcel) -> Decision:
        # Create a context dictionary representing the parcel's data for rule evaluation
        context: Dict[str, Any] = {
            "weight": float(parcel.weight),
            "value": float(parcel.value),
            "country": parcel.country,
        }
        
        # If the parcel has extra attributes, add them to the context
        if parcel.attributes:
            context.update(parcel.attributes)

        # Set default values in case no rules match the parcel
        matched_rule = "default_fallback"
        department = "Manual Review"

        # Evaluate each rule in order of their priority
        for rule in self.rules:
            try:
                # Securely evaluate the condition string (e.g., 'weight > 10') against the context
                # __builtins__: {} blocks dangerous Python commands
                if eval(rule.condition, {"__builtins__": {}}, context):
                    matched_rule = rule.name
                    department = rule.department
                    break
            except Exception:
                # Safely ignore conditions that fail (e.g., missing variables) and check the next rule
                continue

        # Return the final decision formatted exactly as the Pydantic model requires
        return Decision(
            parcel_id=parcel.id or f"pkg-{uuid.uuid4().hex[:8]}",
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