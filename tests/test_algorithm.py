"""Tests of strict Node-RED equivalence, importable without HA installed."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/wetsoil/algorithm.py"
spec = importlib.util.spec_from_file_location("wetsoil_algorithm", SOURCE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def run(**override):
    values = dict(base_seconds=30, max_rain_today=2, max_rain_3d=2,
                  min_temp=23, max_temp=35, rain_today=0,
                  rain_3d=0, temperature=30, raining=False)
    values.update(override)
    return module.calculate(**values)


def test_default_temperature_factor():
    out = run()
    assert out.seconds == 39
    assert out.temp_factor == 1 + 7 / 24


def test_strict_limits():
    assert run(rain_today=2).seconds == 0
    assert run(rain_3d=2).seconds == 0
    assert run(temperature=23).seconds == 0
    assert run(raining=True).seconds == 0


def test_unavailable_is_not_zero():
    assert run(rain_3d=None).seconds is None
    assert run(raining=None).seconds is None
    assert run(temperature=float("nan")).seconds is None


def test_temperature_cap():
    assert run(temperature=35).temp_factor == 1.5
    assert run(temperature=80).seconds == 45


def test_minimum_half_seconds():
    assert run(base_seconds=31, rain_today=1.9).seconds == 15.5


def test_javascript_rounding_half_up():
    assert run(base_seconds=10, temperature=23, min_temp=22, max_temp=24).seconds == 13
    # base 10, factor = 1.25 => 12.5 -> JS Math.round = 13


def test_factors_and_blocked_result():
    out = run(rain_today=1, rain_3d=0.5)
    assert out.rain_today_factor == 0.5
    assert out.rain_3d_factor == 0.75
    assert out.reason == "allowed"
