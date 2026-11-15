"""Pure configuration validation tests."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/wetsoil/const.py"
spec = importlib.util.spec_from_file_location("wetsoil_const", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_defaults_are_independent():
    x, y = module.defaults(), module.defaults()
    assert x["base_seconds"] == 30
    assert x["weekdays"] == [0, 1, 2, 3, 4, 5]
    x["valves"].append("switch.x")
    assert y["valves"] == []


def test_reject_duplicate_valves():
    import pytest
    c = module.defaults()
    c["valves"] = ["switch.x", "switch.x"]
    with pytest.raises(ValueError):
        module.validate_config(c)


def test_reject_nan_and_invalid_chain():
    import pytest
    c = module.defaults()
    c["min_temp"] = float("nan")
    with pytest.raises(ValueError):
        module.validate_config(c)
    c = module.defaults()
    c["start_mode"] = "chained"
    with pytest.raises(ValueError):
        module.validate_config(c)
