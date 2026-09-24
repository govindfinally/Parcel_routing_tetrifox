import yaml
import ast
from pathlib import Path
from typing import List, Set
from pydantic import BaseModel, Field, ValidationError

# Guard 1: Pydantic Model for YAML Rules (Missing fields aur Typos ko rokne ke liye)
class RoutingRule(BaseModel):
    name: str
    priority: int = Field(..., gt=0, description="Priority must be a positive number")
    condition: str
    department: str

# Custom Error Class: Agar YAML mein kuch bhi galat hua, toh yeh error phekega
class RuleLoaderError(Exception):
    pass

def load_rules(file_path: str) -> List[RoutingRule]:
    path = Path(file_path)
    
    # Check if file actually exists
    if not path.is_file():
        raise RuleLoaderError(f"Rule file not found at: {file_path}")
        
    # Guard 2: File Size Limit (Billion Laughs DoS Attack ko rokne ke liye)
    # 1 MB se badi YAML file turant reject ho jayegi
    if path.stat().st_size > 1024 * 1024:
        raise RuleLoaderError("Rule file is too large! Max limit is 1MB.")

    # Read the file text
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuleLoaderError(f"Failed to read file: {str(e)}")

    # Guard 3: Safe Loader (Arbitrary Code Execution se bachne ke liye)
    # Hamesha yaml.safe_load() use karna, yaml.load() nahi!
    try:
        parsed_yaml = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise RuleLoaderError(f"Invalid YAML format. Please check syntax. Error: {str(e)}")

    if not parsed_yaml or 'rules' not in parsed_yaml:
        raise RuleLoaderError("YAML must contain a 'rules' list at the top level.")

    raw_rules = parsed_yaml['rules']
    if not isinstance(raw_rules, list):
        raise RuleLoaderError("'rules' must be a list of rule blocks.")

    validated_rules: List[RoutingRule] = []
    seen_priorities: Set[int] = set()

    for index, raw_rule in enumerate(raw_rules):
        # Guard 4: Pydantic Validation (Checks datatypes and missing keys)
        try:
            rule = RoutingRule(**raw_rule)
        except ValidationError as e:
            # Agar Boss ne 'department' likhna miss kar diya, toh yahan error aayega
            raise RuleLoaderError(f"Rule format error at index {index}: {e.errors()[0]['msg']}")

        # Guard 5: Duplicate Priority Check
        if rule.priority in seen_priorities:
            raise RuleLoaderError(
                f"Duplicate priority '{rule.priority}' in rule '{rule.name}'. Priorities must be unique!"
            )
        seen_priorities.add(rule.priority)

        # Guard 6: Poisoned Logic / Syntax Check
        try:
            # Check karta hai ki condition ek valid Python expression hai ya nahi
            ast.parse(rule.condition, mode='eval')
        except SyntaxError as e:
            raise RuleLoaderError(
                f"Invalid condition logic in rule '{rule.name}': {rule.condition}. Error: {str(e)}"
            )
        
        validated_rules.append(rule)

    # Sabse aakhir mein: Rules ko priority ke hisaab se sort karo (1, 2, 3...)
    validated_rules.sort(key=lambda x: x.priority)
    
    return validated_rules