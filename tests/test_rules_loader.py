import pytest
from app.routing.rules_loader import load_rules, RuleLoaderError

# Pytest ka 'tmp_path' ek magic feature hai jo test ke liye temporary files banata hai
def test_load_valid_rules(tmp_path):
    yaml_content = """
rules:
  - name: "Test Rule"
    priority: 1
    condition: "weight > 10"
    department: "Heavy"
    """
    # Create a temporary yaml file
    file_path = tmp_path / "rules.yaml"
    file_path.write_text(yaml_content)
    
    rules = load_rules(str(file_path))
    assert len(rules) == 1
    assert rules[0].name == "Test Rule"
    assert rules[0].department == "Heavy"

def test_file_not_found():
    with pytest.raises(RuleLoaderError) as exc:
        load_rules("non_existent_fake_file.yaml")
    assert "not found" in str(exc.value)

def test_duplicate_priority(tmp_path):
    yaml_content = """
rules:
  - name: "Rule 1"
    priority: 1
    condition: "weight > 10"
    department: "Heavy"
  - name: "Rule 2"
    priority: 1   # DUPLICATE PRIORITY!
    condition: "value > 10"
    department: "Mail"
    """
    file_path = tmp_path / "bad_rules.yaml"
    file_path.write_text(yaml_content)
    
    with pytest.raises(RuleLoaderError) as exc:
        load_rules(str(file_path))
    assert "Duplicate priority" in str(exc.value)

def test_invalid_syntax_in_condition(tmp_path):
    yaml_content = """
rules:
  - name: "Bad Logic Rule"
    priority: 1
    condition: "weight >>> 10"  # INVALID PYTHON SYNTAX
    department: "Heavy"
    """
    file_path = tmp_path / "syntax_rules.yaml"
    file_path.write_text(yaml_content)
    
    with pytest.raises(RuleLoaderError) as exc:
        load_rules(str(file_path))
    assert "Invalid condition logic" in str(exc.value)

def test_missing_department_field(tmp_path):
    yaml_content = """
rules:
  - name: "Incomplete Rule"
    priority: 1
    condition: "weight > 10"
    # missing 'department' here!
    """
    file_path = tmp_path / "missing_field.yaml"
    file_path.write_text(yaml_content)
    
    with pytest.raises(RuleLoaderError) as exc:
        load_rules(str(file_path))
    assert "Rule format error" in str(exc.value)
    assert "Field required" in str(exc.value)  # FIX: 'department' ki jagah 'Field required' kar diya