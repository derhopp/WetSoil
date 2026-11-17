"""Pure configuration validation tests."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/wetsoil/const.py"
spec = importlib.util.spec_from_file_location("wetsoil_const", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_defaults_are_independent():
    x, y = module.defaults(), module.defaults()
    assert x["base_seconds"] == 1800
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


def test_intensity_config_mode_is_valid():
    c = module.defaults()
    c["precipitation_sensor_kind"] = "intensity"
    c["precipitation_sensor"] = "sensor.actual_precipitation_intensity"
    result = module.validate_config(c)
    assert result["precipitation_sensor_kind"] == "intensity"


def test_numeric_limits_use_same_precision_as_weather_measurements():
    sample = module.defaults()
    sample["max_rain_today"] = 1.999
    sample["max_rain_3d"] = 4.666
    sample["min_temp"] = 20.04
    sample["max_temp"] = 34.96
    normalized = module.validate_config(sample)
    assert normalized["max_rain_today"] == 2.00
    assert normalized["max_rain_3d"] == 4.67
    assert normalized["min_temp"] == 20.0
    assert normalized["max_temp"] == 35.0


def test_existing_configured_base_duration_is_not_overwritten_by_new_default():
    existing = module.defaults()
    existing["base_seconds"] = 30.0
    assert module.validate_config(existing)["base_seconds"] == 30.0
    assert module.defaults()["base_seconds"] == 1800.0
