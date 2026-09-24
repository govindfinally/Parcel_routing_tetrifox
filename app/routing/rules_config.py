from typing import List
from app.routing.rules_loader import load_rules, RoutingRule

class RulesConfig:
    _rules: List[RoutingRule] = []

    @classmethod
    def load(cls, file_path: str = "config/rules.yaml"):
        cls._rules = load_rules(file_path)
        print(f"Successfully loaded {len(cls._rules)} rules into memory.")

    @classmethod
    def get_rules(cls) -> List[RoutingRule]:
        if not cls._rules:
            raise ValueError("Rules have not been loaded into memory yet!")
        return cls._rules