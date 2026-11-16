"""Precision contract for user-visible meteorological thresholds."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location(
    "wetsoil_precision_algorithm",
    Path(__file__).resolve().parents[1]/"custom_components/wetsoil/algorithm.py",
)
module=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=module
spec.loader.exec_module(module)


def test_precipitation_rounds_to_two_decimals_for_threshold():
    result=module.calculate(120,2,10,20,35,1.9999,0.0,25,False)
    assert result.reason=="rain_today_limit"
    assert result.seconds==0


def test_temperature_rounds_to_one_decimal_for_threshold():
    result=module.calculate(120,5,10,25,35,0.0,0.0,25.04,False)
    assert result.reason=="temperature_limit"


def test_missing_readings_still_unavailable():
    assert module.calculate(120,5,10,25,35,None,0,25,False).seconds is None
