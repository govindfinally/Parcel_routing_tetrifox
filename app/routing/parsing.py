import html
from typing import Any, Dict, List

def sanitize_string(value: str) -> str:
    value = value.replace("\x00", "")
    return html.escape(value)

def sanitize_list(items: List[Any], max_depth: int, current_depth: int) -> List[Any]:
    if current_depth > max_depth:
        raise ValueError("Payload exceeds maximum allowed nesting depth")

    sanitized = []
    for item in items:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_payload(item, max_depth, current_depth + 1))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, max_depth, current_depth + 1))
        else:
            sanitized.append(item)
    return sanitized

def sanitize_payload(payload: Dict[str, Any], max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
    if current_depth > max_depth:
        raise ValueError("Payload exceeds maximum allowed nesting depth")

    sanitized = {}
    for key, value in payload.items():
        safe_key = sanitize_string(key)
        
        if isinstance(value, str):
            sanitized[safe_key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_payload(value, max_depth, current_depth + 1)
        elif isinstance(value, list):
            sanitized[safe_key] = sanitize_list(value, max_depth, current_depth + 1)
        else:
            sanitized[safe_key] = value

    return sanitized