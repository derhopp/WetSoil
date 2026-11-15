"""Isolated pure weather/history tests without a Home Assistant installation."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from types import ModuleType

import pytest


class FakeStore:
    """In-memory clone of HA's storage interface."""
    data = {}

    def __init__(self, hass, version, key):
        self.key = key

    async def async_load(self):
        return self.data.get(self.key)

    async def async_save(self, value):
        self.data[self.key] = value


@pytest.fixture()
def weather(monkeypatch):
    """Load weather.py against a minimal isolated HA interface."""
    modules = {
        key: ModuleType(key) for key in (
            "homeassistant", "homeassistant.helpers",
            "homeassistant.helpers.storage", "homeassistant.util",
            "homeassistant.util.dt"
        )
    }
    modules["homeassistant.helpers.storage"].Store = FakeStore
    dt = modules["homeassistant.util.dt"]
    dt.as_local = lambda value: value.astimezone(timezone.utc)
    dt.now = lambda: datetime.now(timezone.utc)
    for key, module in modules.items():
        monkeypatch.setitem(sys.modules, key, module)
    path = (Path(__file__).resolve().parents[1]
            / "custom_components/wetsoil/weather.py")
    spec = importlib.util.spec_from_file_location("wetsoil_weather_unit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    FakeStore.data = {}
    return module


def test_units_and_invalid(weather):
    assert weather.as_mm(1, "in") == 25.4
    assert weather.as_mm(2, "cm") == 20
    assert weather.as_mm(-1, "mm") is None
    assert weather.as_mm("unknown", "mm") is None
    assert weather.as_mm(1, "unknown") is None
    assert weather.as_celsius(68, "°F") == 20
    assert weather.as_celsius(22, "°C") == 22


def test_daily_forecast_date_and_units(weather):
    rows = [
        {"datetime": "2026-11-14T00:00:00+00:00", "temperature": 50,
         "precipitation": 0.1},
        {"datetime": "2026-11-15T00:00:00+00:00", "temperature": 77,
         "precipitation": 1},
    ]
    target = datetime(2026, 11, 15, tzinfo=timezone.utc).date()
    assert weather.daily_forecast(rows, target, "in", "°F") == (25, 25.4)
    assert weather.daily_forecast(rows, target - timedelta(days=10), "mm", "°C") == (None, None)


@pytest.mark.asyncio
async def test_historical_three_complete_days(weather):
    history = weather.RainfallHistory(None, "test")
    await history.restore()
    first = datetime(2026, 11, 10, tzinfo=timezone.utc)
    for index in range(3 * 288 + 1):
        when = first + timedelta(minutes=5 * index)
        await history.sample(when, (index % 288) / 100, "daily")
    today = (first + timedelta(days=3)).date()
    assert history.three_day_mean(today) == pytest.approx(2.87)
    restored = weather.RainfallHistory(None, "test")
    await restored.restore()
    assert restored.three_day_mean(today) == pytest.approx(2.87)


@pytest.mark.asyncio
async def test_missing_samples_prevent_valid_history(weather):
    history = weather.RainfallHistory(None, "gap")
    when = datetime(2026, 11, 10, tzinfo=timezone.utc)
    await history.sample(when, 1.0, "total")
    await history.sample(when + timedelta(hours=3), 1.2, "total")
    await history.sample(when + timedelta(days=1), 1.3, "total")
    assert history.days == {}


@pytest.mark.asyncio
async def test_counter_reset_marks_day_invalid(weather):
    history = weather.RainfallHistory(None, "reset")
    first = datetime(2026, 11, 10, tzinfo=timezone.utc)
    for index in range(289):
        when = first + timedelta(minutes=5 * index)
        amount = index / 100 if index < 150 else (index - 150) / 100
        await history.sample(when, amount, "total")
    assert history.days == {}
