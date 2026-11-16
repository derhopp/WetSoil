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
    circuit._owned_valves = set()
    circuit.error = None
    circuit.status = "idle"
    circuit.running = False
    circuit.kind = None
    circuit._task = None
    circuit.lock = asyncio.Lock()
    circuit.events = []
    circuit.ended = None
    circuit.ends = None
    circuit.entry = SimpleNamespace(entry_id="test")
    circuit._save = lambda: asyncio.sleep(0)
    circuit.changed = lambda: None
    circuit._successor = lambda: asyncio.sleep(0)
    return circuit



@pytest.mark.asyncio
async def test_no_off_during_idle_even_if_actuator_is_on(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    await circuit.stop("manual_stop")
    assert hass.calls == []


@pytest.mark.asyncio
async def test_off_only_on_explicit_stop_of_owned_run(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.running = True
    circuit.kind = "manual"
    circuit._owned_valves = {"switch.test_valve"}
    await circuit.stop("manual_stop")
    assert hass.calls == [("switch","turn_off","switch.test_valve")]


@pytest.mark.asyncio
async def test_normal_completion_sends_single_off(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.running = True
    circuit.kind = "manual"
    circuit._owned_valves = {"switch.test_valve"}
    await circuit.stop("complete",abort=False)
    assert len(hass.calls) == 1
    assert circuit.status == "idle"


@pytest.mark.asyncio
async def test_shutdown_does_not_switch_off_owned_actuators(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.running = True
    circuit.kind = "auto"
    circuit._owned_valves = {"switch.test_valve"}
    circuit._unsub = []
    circuit._closed = False
    await circuit.shutdown()
    assert hass.calls == []
    assert circuit.running is False
    assert circuit._owned_valves == set()


@pytest.mark.asyncio
async def test_start_must_not_take_over_externally_on_valve(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.weather = SimpleNamespace(update=lambda cfg: asyncio.sleep(0), rain_blocked=False)
    circuit.calculation = lambda: SimpleNamespace(seconds=30)
    circuit.config = {"valves":["switch.test_valve"],"base_seconds":30,
                      "max_runtime":60}
    with pytest.raises(RuntimeError,match="valve_not_off"):
        await circuit.start(manual=True)
    assert hass.calls == []


@pytest.mark.asyncio
async def test_off_service_failure_does_not_retry_or_lockout(circuit_class):
    hass = MockHass("on")
    async def fail(h):
        raise RuntimeError("device offline")
    hass.on_call = fail
    circuit = make_circuit(circuit_class, hass)
    circuit.running = True
    circuit._owned_valves = {"switch.test_valve"}
    await circuit.stop()
    assert len(hass.calls) == 1
    assert circuit.error == "stop_command_failed:switch.test_valve"
    assert not hasattr(circuit,"recovery_required")


@pytest.mark.asyncio
async def test_start_failure_can_be_followed_by_explicit_stop(circuit_class):
    hass = MockHass("off")
    async def fail_first(h):
        if h.calls[-1][1] == "turn_on":
            raise RuntimeError("on service failed")
    hass.on_call = fail_first
    circuit = make_circuit(circuit_class, hass)
    circuit.weather = SimpleNamespace(update=lambda cfg: asyncio.sleep(0), rain_blocked=False)
    circuit.calculation = lambda: SimpleNamespace(seconds=30)
    circuit.config = {"valves":["switch.test_valve"],"base_seconds":30,
                      "max_runtime":60}
    with pytest.raises(RuntimeError,match="start_failed"):
        await circuit.start(manual=True)
    assert [item[1] for item in hass.calls] == ["turn_on"]
    assert circuit._owned_valves == {"switch.test_valve"}
    await circuit.stop()
    assert [item[1] for item in hass.calls] == ["turn_on","turn_off"]
