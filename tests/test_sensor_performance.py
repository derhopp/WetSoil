"""Regression guard: individual WetSoil sensors must not build snapshots."""
import ast
from pathlib import Path


def test_native_sensor_value_does_not_call_whole_circuit_snapshot():
    filename = (Path(__file__).resolve().parents[1]
                / "custom_components/wetsoil/sensor.py")
    tree = ast.parse(filename.read_text(encoding="utf-8"))
    native_methods = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "native_value"
    ]
    assert len(native_methods) == 1
    for node in ast.walk(native_methods[0]):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != "snapshot"
