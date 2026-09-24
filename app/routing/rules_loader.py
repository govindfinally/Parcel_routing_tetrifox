import ast
import yaml
from typing import List
from pydantic import BaseModel, ValidationError
from app.core.logging import setup_logger

logger = setup_logger(__name__)

class RoutingRule(BaseModel):
    name: str
    priority: int
    condition: str
    department: str

class RuleLoaderError(Exception):
    pass

def load_rules(file_path: str) -> List[RoutingRule]:
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        if not data or "rules" not in data:
            raise RuleLoaderError("YAML file must contain a 'rules' key")

        rules = []
        priorities = set()

        for i, rule_data in enumerate(data["rules"]):
            # 1. Basic Pydantic Schema Validation
            try:
                rule = RoutingRule(**rule_data)
            except ValidationError as e:
                raise RuleLoaderError(
                    f"Rule format error at index {i}: {e.errors()[0]['msg']}"
                ) from e

            # 2. Prevent Duplicate Priorities
            if rule.priority in priorities:
                raise RuleLoaderError(
                    f"Duplicate priority: {rule.priority}"
                )
            priorities.add(rule.priority)

            # 3. Validate Python Syntax for the Condition
            try:
                ast.parse(rule.condition, mode="eval")
            except SyntaxError as e:
                raise RuleLoaderError(
                    f"Invalid condition logic at index {i}: {e.msg}"
                ) from e

            rules.append(rule)

        sorted_rules = sorted(rules, key=lambda rule: rule.priority)
        logger.info(
            "Successfully validated and sorted %d rules.",
            len(sorted_rules),
        )
        return sorted_rules

    except FileNotFoundError as e:
        logger.error("Rules file not found at %s", file_path)
        raise RuleLoaderError(
            f"Rules file not found at {file_path}"
        ) from e
    except yaml.YAMLError as e:
        logger.error("Invalid YAML syntax: %s", e)
        raise RuleLoaderError(f"Invalid YAML syntax: {e}") from e