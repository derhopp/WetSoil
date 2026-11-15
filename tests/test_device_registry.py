"""Protect against reintroducing the deprecated DeviceRegistry lookup."""
import ast
from pathlib import Path


def test_device_lookup_is_config_entry_scoped():
    path = Path(__file__).resolve().parents[1] / "custom_components/wetsoil/__init__.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"async_get_device", "async_get_device_by_identifier"}
    ]
    assert all(node.func.attr != "async_get_device" for node in calls)
    assert len(calls) == 1
    lookup = calls[0]
    assert lookup.func.attr == "async_get_device_by_identifier"
    assert len(lookup.args) == 2
    assert isinstance(lookup.args[0], ast.Tuple)
    assert isinstance(lookup.args[0].elts[0], ast.Name)
    assert lookup.args[0].elts[0].id == "DOMAIN"
    assert isinstance(lookup.args[1], ast.Attribute)
    assert lookup.args[1].attr == "entry_id"
