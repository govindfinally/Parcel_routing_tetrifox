import pytest
from app.routing.parsing import sanitize_string, sanitize_payload

def test_sanitize_string_removes_null_bytes_and_escapes_html():
    raw_input = "<script>alert('xss')</script>\x00"
    expected = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert sanitize_string(raw_input) == expected

def test_sanitize_payload_handles_flat_dictionary():
    payload = {"name\x00": "<b>Bold</b>", "age": 25, "active": True}
    expected = {"name": "&lt;b&gt;Bold&lt;/b&gt;", "age": 25, "active": True}
    assert sanitize_payload(payload) == expected

def test_sanitize_payload_handles_nested_lists_and_dicts():
    payload = {
        "data": {
            "tags": ["<admin>", "user\x00"],
            "metadata": {"key": "val<ue>"}
        }
    }
    expected = {
        "data": {
            "tags": ["&lt;admin&gt;", "user"],
            "metadata": {"key": "val&lt;ue&gt;"}
        }
    }
    assert sanitize_payload(payload) == expected

def test_sanitize_payload_enforces_dict_depth_limit():
    payload = {"level1": {"level2": {"level3": {"level4": {"level5": "data"}}}}}
    with pytest.raises(ValueError) as exc:
        sanitize_payload(payload, max_depth=3)
    assert "Payload exceeds maximum allowed nesting depth" in str(exc.value)

def test_sanitize_payload_enforces_list_depth_limit():
    payload = {"data": [[[["deep nested string"]]]]}
    with pytest.raises(ValueError) as exc:
        sanitize_payload(payload, max_depth=2)
    assert "Payload exceeds maximum allowed nesting depth" in str(exc.value)