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


class FakeState:
    def __init__(self, state):
        self.state = state


class FakeRainHass:
    def __init__(self, states):
        self.states = self
        self.values = {name: FakeState(value) for name, value in states.items()}

    def get(self, entity):
        return self.values.get(entity)


def test_dry_sensor_is_displayed_as_dry_even_if_weather_reports_rain(weather):
    hass = FakeRainHass({
        "weather.station": "rainy",
        "binary_sensor.rain": "off",
    })
    sample = weather.WetSoilWeather(hass, "rain-test")
    config = {"weather_entity": "weather.station",
              "rain_sensor": "binary_sensor.rain"}
    assert sample.read_rain(config) is False
    assert sample.raining is False
    assert sample.weather_raining is True
    assert sample.sensor_raining is False
    assert sample.rain_source_disagreement is True
    assert sample.rain_blocked is None


def test_wet_sensor_without_weather_conflict_blocks_watering(weather):
    hass = FakeRainHass({
        "weather.station": "rainy", "binary_sensor.rain": "on",
    })
    sample = weather.WetSoilWeather(hass, "wet-test")
    assert sample.read_rain({
        "weather_entity": "weather.station", "rain_sensor": "binary_sensor.rain",
    }) is True
    assert sample.rain_source_disagreement is False
    assert sample.rain_blocked is True


def test_unknown_rain_sensor_does_not_silently_become_dry(weather):
    hass = FakeRainHass({
        "weather.station": "sunny", "binary_sensor.rain": "unavailable",
    })
    sample = weather.WetSoilWeather(hass, "unknown-test")
    assert sample.read_rain({
        "weather_entity": "weather.station", "rain_sensor": "binary_sensor.rain",
    }) is None
    assert sample.rain_blocked is None


def test_weather_fallback_when_no_binary_rain_sensor(weather):
    hass = FakeRainHass({"weather.station": "rainy"})
    sample = weather.WetSoilWeather(hass, "fallback-test")
    assert sample.read_rain({
        "weather_entity": "weather.station", "rain_sensor": None,
    }) is True
    assert sample.rain_blocked is True
    hass.values["weather.station"] = FakeState("sunny")
    assert sample.read_rain({
        "weather_entity": "weather.station", "rain_sensor": None,
    }) is False
    assert sample.rain_blocked is False


@pytest.mark.asyncio
async def test_provider_switch_immediately_fetches_daily_only_source(weather, monkeypatch):
    """A recently fetched provider must never block or contaminate a new one."""
    fixed = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
    sys.modules["homeassistant.util.dt"].now = lambda: fixed
    requests = []

    class State:
        def __init__(self, value):
            self.state = value
            self.attributes = {"temperature_unit": "°C", "precipitation_unit": "mm"}

    class Services:
        async def async_call(self, domain, service, data, **kwargs):
            requests.append((data["entity_id"], data["type"]))
            if data["entity_id"] == "weather.iwolfe67" and data["type"] == "hourly":
                raise RuntimeError("hourly forecast not supported")
            if data["type"] == "hourly":
                return {data["entity_id"]: {"forecast": [
                    {"datetime":"2026-11-16T12:00:00+00:00",
                     "temperature":30,"precipitation":3}
                ]}}
            t, p = (18, 4) if data["entity_id"] == "weather.home" else (24, 1)
            return {data["entity_id"]: {"forecast": [
                {"datetime":"2026-11-16T00:00:00+00:00",
                 "temperature":t,"precipitation":p}
            ]}}

    class Hass:
        services = Services()
        states = None
        def __init__(self):
            self.states = self
        def get(self, entity):
            return State("sunny")
    hass=Hass()
    data=weather.WetSoilWeather(hass,"provider-test")
    config={"weather_entity":"weather.home","rain_sensor":None,
            "precipitation_sensor":None,"precipitation_sensor_kind":"daily"}
    await data.update(config)
    assert (data.temperature,data.rain_today,data.forecast_source)==(18,4,"daily")
    assert data.forecast_entity=="weather.home"
    config["weather_entity"]="weather.iwolfe67"
    await data.update(config)  # Same instant: bypass old 30-minute throttle
    assert (data.temperature,data.rain_today,data.forecast_source)==(24,1,"daily")
    assert data.forecast_entity=="weather.iwolfe67"
    assert requests==[
        ("weather.home","hourly"),("weather.home","daily"),
        ("weather.iwolfe67","hourly"),("weather.iwolfe67","daily")
    ]


def test_hourly_forecast_requires_complete_day(weather):
    from zoneinfo import ZoneInfo
    tz=ZoneInfo("Europe/Berlin")
    day=datetime(2026,11,16,tzinfo=tz).date()
    start=datetime(2026,11,15,23,0,tzinfo=timezone.utc)
    rows=[
        {"datetime":(start+timedelta(hours=i)).isoformat(),
         "temperature":15+i/10,"precipitation":0.1}
        for i in range(24)
    ]
    temp,rain=weather.hourly_forecast(rows,day,"mm","°C",tz)
    assert temp==pytest.approx(17.3)
    assert rain==pytest.approx(2.4)
    assert weather.hourly_forecast(rows[1:],day,"mm","°C",tz)==(None,None)


def test_hourly_forecast_handles_daylight_saving_changes(weather):
    from zoneinfo import ZoneInfo
    tz=ZoneInfo("Europe/Berlin")
    for target, start, hours in [
        (datetime(2026,3,29).date(),datetime(2026,3,28,23,tzinfo=timezone.utc),23),
        (datetime(2026,10,25).date(),datetime(2026,10,24,22,tzinfo=timezone.utc),25),
    ]:
        rows=[{"datetime":(start+timedelta(hours=i)).isoformat(),
               "temperature":20,"precipitation":0.2} for i in range(hours)]
        assert weather.hourly_forecast(rows,target,"mm","°C",tz)==pytest.approx((20,hours*0.2))
