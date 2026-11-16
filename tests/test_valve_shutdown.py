"""Tests for startup safety checks and valve OFF confirmation semantics."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture()
def circuit_class(monkeypatch):
    """Load controller in isolation with tiny HA test doubles."""
    base = Path(__file__).resolve().parents[1] / "custom_components/wetsoil"
    modules = {
        name: ModuleType(name) for name in (
            "homeassistant", "homeassistant.core", "homeassistant.helpers",
            "homeassistant.helpers.event", "homeassistant.helpers.storage",
            "homeassistant.util", "homeassistant.util.dt",
        )
    }
    modules["homeassistant.core"].callback = lambda fn: fn
    modules["homeassistant.helpers.event"].async_track_state_change_event = lambda *a: None
    modules["homeassistant.helpers.event"].async_track_time_interval = lambda *a: None
    modules["homeassistant.helpers.storage"].Store = object
    dt = modules["homeassistant.util.dt"]
    dt.now = lambda: None
    dt.utcnow = lambda: None
    dt.as_local = lambda x: x
    dt.parse_datetime = lambda x: None
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    package = ModuleType("wetsoil_off_test")
    package.__path__ = [str(base)]
    monkeypatch.setitem(sys.modules, "wetsoil_off_test", package)
    for name in ("const", "algorithm", "schedule"):
        spec = importlib.util.spec_from_file_location(
            f"wetsoil_off_test.{name}", base / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
    weather_stub = ModuleType("wetsoil_off_test.weather")
    weather_stub.WetSoilWeather = object
    monkeypatch.setitem(sys.modules, weather_stub.__name__, weather_stub)
    spec = importlib.util.spec_from_file_location(
        "wetsoil_off_test.controller", base / "controller.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Circuit


class MockHass:
    def __init__(self, initial):
        self.values = {"switch.test_valve": initial}
        self.calls = []
        self.states = self
        self.services = SimpleNamespace(async_call=self.call)
        self.on_call = None

    def get(self, entity):
        state = self.values.get(entity)
        return SimpleNamespace(state=state) if state is not None else None

    async def call(self, domain, service, data, blocking=False):
        self.calls.append((domain, service, data["entity_id"]))
        if self.on_call:
            await self.on_call(self)


def make_circuit(cls, hass):
    circuit = cls.__new__(cls)
    circuit.hass = hass
    circuit.config = {"valves": ["switch.test_valve"]}
    circuit.recovery_required = False
    circuit.error = None
    circuit.status = "idle"
    circuit.running = False
    circuit.OFF_CONFIRM_TIMEOUT = 0.05
    circuit.OFF_POLL_INTERVAL = 0.005
    return circuit


@pytest.mark.asyncio
async def test_off_at_startup_does_not_call_service(circuit_class):
    hass = MockHass("off")
    circuit = make_circuit(circuit_class, hass)
    assert await circuit._off() is True
    assert hass.calls == []
    assert circuit.error is None
    assert circuit.recovery_required is False


@pytest.mark.asyncio
async def test_delayed_off_state_is_confirmed(circuit_class):
    hass = MockHass("on")
    async def on_call(h):
        asyncio.get_running_loop().call_later(
            0.01, lambda: h.values.__setitem__("switch.test_valve", "off")
        )
    hass.on_call = on_call
    circuit = make_circuit(circuit_class, hass)
    assert await circuit._off() is True
    assert len(hass.calls) == 1
    assert circuit.recovery_required is False


@pytest.mark.asyncio
async def test_unknown_valve_stays_blocked(circuit_class):
    hass = MockHass(None)
    circuit = make_circuit(circuit_class, hass)
    assert await circuit._off() is False
    assert len(hass.calls) == 2
    assert circuit.recovery_required is True
    assert circuit.status == "error"
    assert circuit.error == "shutdown_unconfirmed:switch.test_valve"


@pytest.mark.asyncio
async def test_stale_shutdown_error_clears_only_after_confirmed_off(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.recovery_required = True
    circuit.error = "shutdown_unconfirmed:switch.test_valve"
    circuit.status = "error"
    assert await circuit._off() is False
    assert circuit.error == "shutdown_unconfirmed:switch.test_valve"
    hass.values["switch.test_valve"] = "off"
    assert await circuit._off() is True
    assert circuit.error is None
    assert circuit.status == "idle"
    assert circuit.recovery_required is False


@pytest.mark.asyncio
async def test_service_error_with_off_feedback_is_success(circuit_class):
    hass = MockHass("on")
    async def on_call(h):
        h.values["switch.test_valve"] = "off"
        raise RuntimeError("service reply lost")
    hass.on_call = on_call
    circuit = make_circuit(circuit_class, hass)
    assert await circuit._off() is True
    assert len(hass.calls) == 1


@pytest.mark.asyncio
async def test_unrelated_error_is_not_hidden_by_off_check(circuit_class):
    hass = MockHass("off")
    circuit = make_circuit(circuit_class, hass)
    circuit.error = "rain_or_unknown"
    circuit.status = "error"
    assert await circuit._off() is True
    assert circuit.error == "rain_or_unknown"
    assert circuit.status == "error"
