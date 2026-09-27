import pytest
from app.routing.models import Parcel
from app.routing.rules_config import RulesConfig
from app.routing.engine import RoutingEngine

@pytest.fixture(autouse=True)
def setup_test_rules(tmp_path):
    yaml_content = """
rules:
  - name: "High Value Insurance"
    priority: 1
    condition: "value > 1000"
    department: "Insurance"
  - name: "Lightweight Mail"
    priority: 2
    condition: "weight <= 1"
    department: "Mail"
  - name: "Liquid Handling"
    priority: 3
    condition: "is_liquid == True"
    department: "Hazmat"
    """
    file_path = tmp_path / "test_rules.yaml"
    file_path.write_text(yaml_content)
    RulesConfig.load(str(file_path))

def test_priority_override():
    engine = RoutingEngine()
    parcel = Parcel(weight="0.5", value="2000", country="US")
    
    decision = engine.route(parcel)
    
    assert decision.department == "Insurance"
    assert decision.matched_rule == "High Value Insurance"

def test_standard_match():
    engine = RoutingEngine()
    parcel = Parcel(weight="0.5", value="100", country="US")
    
    decision = engine.route(parcel)
    
    assert decision.department == "Mail"
    assert decision.matched_rule == "Lightweight Mail"

def test_fallback_no_match():
    engine = RoutingEngine()
    parcel = Parcel(weight="5.0", value="100", country="US")
    
    decision = engine.route(parcel)
    
    assert decision.department == "Manual Review"
    assert decision.matched_rule == "default_fallback"

def test_dynamic_attributes():
    engine = RoutingEngine()
    parcel = Parcel(weight="5.0", value="100", country="US", attributes={"is_liquid": True})
    
    decision = engine.route(parcel)
    
    assert decision.department == "Hazmat"
    assert decision.matched_rule == "Liquid Handling"

def test_safe_evaluation_on_missing_attributes():
    engine = RoutingEngine()
    parcel = Parcel(weight="5.0", value="100", country="US")
    
    decision = engine.route(parcel)
    
    assert decision.department == "Manual Review"
@pytest.fixture(autouse=True)
def setup_test_rules(tmp_path):
    yaml_content = """
rules:
  - name: "Fragile Handling"
    priority: 0
    condition: "fragile == True"
    department: "Fragile"
  - name: "High Value Insurance"
    priority: 1
    condition: "value > 1000"
    department: "Insurance"
  - name: "Lightweight Mail"
    priority: 2
    condition: "weight <= 1"
    department: "Mail"
  - name: "Liquid Handling"
    priority: 3
    condition: "is_liquid == True"
    department: "Hazmat"
  - name: "Tie Alpha"
    priority: 4
    condition: "weight > 100"
    department: "Zulu"
  - name: "Tie Beta"
    priority: 5
    condition: "weight > 100"
    department: "Alpha"
    """
    file_path = tmp_path / "test_rules.yaml"
    file_path.write_text(yaml_content)
    RulesConfig.load(str(file_path))


def test_fragile_overrides_all_other_rules():
    engine = RoutingEngine()
    # value > 1000 would also match Insurance, but fragile must win
    parcel = Parcel(weight="0.5", value="2000", country="US", fragile=True)
    decision = engine.route(parcel)
    assert decision.department == "Fragile"
    assert decision.matched_rule == "Fragile Handling"


def test_multi_match_resolves_alphabetically():
    engine = RoutingEngine()
    # weight=150 matches BOTH "Tie Alpha" (Zulu) and "Tie Beta" (Alpha)
    parcel = Parcel(weight="150", value="10", country="US")
    decision = engine.route(parcel)
    assert decision.department == "Alpha"  # alphabetically first, not priority-first