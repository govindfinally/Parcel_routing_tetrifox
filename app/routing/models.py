import re
from decimal import Decimal
from typing import Optional, Dict, Union, Literal, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError

class Parcel(BaseModel):
    model_config = ConfigDict(
        extra='forbid', 
        str_strip_whitespace=True
    )

    id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._-]+$', max_length=64)
    weight: Decimal = Field(..., gt=0, le=1000, decimal_places=6)
    value: Decimal = Field(..., ge=0, le=10000000, decimal_places=4)
    country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$')
    
    attributes: Optional[Dict[str, Union[str, int, float, bool, None]]] = Field(
        default=None, 
        max_length=20
    )

    @field_validator('id', mode='before')
    @classmethod
    def empty_id_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('weight', 'value', mode='before')
    @classmethod
    def strict_number_types(cls, v: Any) -> Any:
        if isinstance(v, bool):
            raise ValueError("must be a valid number, not a boolean")
        if isinstance(v, str) and len(v) > 32:
            raise ValueError("number string exceeds maximum length of 32 characters")
        return v

    @field_validator('weight', 'value', mode='after')
    @classmethod
    def reject_nan_infinity(cls, v: Decimal) -> Decimal:
        if v.is_nan() or v.is_infinite():
            raise ValueError("NaN and Infinity are not allowed")
        return v

    @field_validator('country', mode='before')
    @classmethod
    def normalize_country(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator('attributes')
    @classmethod
    def validate_attributes(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not v:
            return v
            
        key_regex = re.compile(r'^[A-Za-z0-9_]{1,40}$')
        for key, val in v.items():
            if not key_regex.match(key):
                raise ValueError(f"invalid key format: {key}")
            if isinstance(val, str) and len(val) > 200:
                raise ValueError(f"string value for '{key}' exceeds 200 characters")
        return v


class Decision(BaseModel):
    parcel_id: str
    weight_kg: str
    value_eur: str
    department: str
    status: Literal["ROUTED", "PENDING_APPROVAL"]
    approvals_required: List[str]
    matched_rule: str
    gates_triggered: List[str]
    reason: str
    ruleset_version: str


def format_validation_errors(exc: ValidationError) -> List[str]:
    formatted_errors = []
    for error in exc.errors():
        loc = ".".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "")
        
        # Pydantic v2 prepends "Value error, " for custom validators. We strip it for readability.
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
            
        # Pydantic native messages use "Input should be". We change it to "must be" to avoid echoing inputs.
        if "Input should be" in msg:
            msg = msg.replace("Input should be", "must be")
            
        formatted_errors.append(f"{loc}: {msg}")
        
    return formatted_errors