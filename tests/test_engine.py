import pytest
from decimal import Decimal
from pydantic import ValidationError
from app.routing.models import Parcel, Decision, format_validation_errors

def test_weight_boundaries():
    # Valid boundaries
    parcel = Parcel(weight="0.000001", value="10", country="DE")
    assert parcel.weight == Decimal("0.000001")
    
    parcel = Parcel(weight="1000", value="10", country="DE")
    assert parcel.weight == Decimal("1000")

    # Invalid boundaries
    with pytest.raises(ValidationError) as exc:
        Parcel(weight="0", value="10", country="DE")
    assert "weight" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Parcel(weight="1000.01", value="10", country="DE")
    assert "weight" in str(exc.value)


def test_value_boundaries():
    # Valid boundaries
    parcel = Parcel(weight="5", value="0", country="DE")
    assert parcel.value == Decimal("0")

    # Invalid boundaries
    with pytest.raises(ValidationError) as exc:
        Parcel(weight="5", value="-1", country="DE")
    assert "value" in str(exc.value)


def test_country_normalization_and_validation():
    # 'nl' should become 'NL'
    parcel = Parcel(weight="5", value="10", country="nl")
    assert parcel.country == "NL"

    # 'NLD' should be rejected
    with pytest.raises(ValidationError) as exc:
        Parcel(weight="5", value="10", country="NLD")
    assert "country" in str(exc.value)


def test_reject_unknown_fields():
    with pytest.raises(ValidationError) as exc:
        Parcel(weight="5", value="10", unknown_field="test")
    assert "unknown_field" in str(exc.value)
    assert "Extra inputs are not permitted" in str(exc.value)


def test_reject_nan_and_infinity():
    with pytest.raises(ValidationError) as exc:
        Parcel(weight="NaN", value="10")
    assert "finite number" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Parcel(weight="5", value="Infinity")
    assert "finite number" in str(exc.value)


def test_reject_boolean_for_numeric_fields():
    with pytest.raises(ValidationError) as exc:
        Parcel(weight=True, value="10")
    assert "must be a valid number, not a boolean" in str(exc.value)


def test_reject_excessive_number_string_length():
    long_num = "1" * 33
    with pytest.raises(ValidationError) as exc:
        Parcel(weight=long_num, value="10")
    assert "exceeds maximum length" in str(exc.value)


def test_format_validation_errors_hides_input():
    secret_bad_value = "-99998888.55"
    
    with pytest.raises(ValidationError) as exc:
        # Intentionally failing validation with a highly specific value
        Parcel(weight=secret_bad_value, value="10")
        
    errors = format_validation_errors(exc.value)
    
    # 1. Ensure the output is correctly formatted
    assert len(errors) > 0
    assert any("weight: must be greater than 0" in e for e in errors)
    
    # 2. Ensure the actual input string NEVER appears in the formatted output
    for error_msg in errors:
        assert secret_bad_value not in error_msg


def test_decision_model_success():
    # Validates that 'department' is accepted as a plain string, not enforcing an Enum
    decision = Decision(
        parcel_id="PKG-123",
        weight_kg="5.5",
        value_eur="100.0",
        department="Custom Operations Department", 
        status="ROUTED",
        approvals_required=[],
        matched_rule="regular_rule_01",
        gates_triggered=[],
        reason="Matched base criteria",
        ruleset_version="v1.0.0"
    )
    assert decision.department == "Custom Operations Department"