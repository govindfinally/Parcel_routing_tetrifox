import yaml
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
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
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            
        if not data or 'rules' not in data:
            raise RuleLoaderError("YAML file must contain a 'rules' key")
            
        rules = []
        for i, rule_data in enumerate(data['rules']):
            try:
                rule = RoutingRule(**rule_data)
                rules.append(rule)
            except ValidationError as e:
                raise RuleLoaderError(f"Rule format error at index {i}: {e.errors()[0]['msg']}")
                
        sorted_rules = sorted(rules, key=lambda x: x.priority)
        logger.info(f"Successfully validated and sorted {len(sorted_rules)} rules.")
        return sorted_rules
        
    except FileNotFoundError:
        logger.error(f"Rules file not found at {file_path}")
        raise RuleLoaderError(f"Rules file not found at {file_path}")
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax: {str(e)}")
        raise RuleLoaderError(f"Invalid YAML syntax: {str(e)}")