"""Tests for startup safety checks and valve OFF confirmation semantics."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
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
    dt.utcnow = lambda: datetime.now(timezone.utc)
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
    circuit._automatic_lock = asyncio.Lock()
    circuit._closed = False
    circuit.last_slot = None
    circuit.last_started_date = None
    circuit.last_auto_run_date = None
    circuit.last_run_at = None
    circuit.last_run_kind = None
    circuit.last_skip_at = None
    circuit.last_skip_reason = None
    circuit.last_attempt = None
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


@pytest.mark.asyncio
async def test_rain_event_does_not_interfere_with_active_or_external_actuator(circuit_class):
    hass = MockHass("on")
    circuit = make_circuit(circuit_class, hass)
    circuit.running = True
    circuit._owned_valves = {"switch.test_valve"}
    circuit.weather = SimpleNamespace(
        read_rain=lambda cfg: None, rain_blocked=True
    )
    circuit.config["rain_sensor"] = "binary_sensor.rain"
    circuit.config["precipitation_sensor"] = None
    circuit.config["weather_entity"] = None
    await circuit._check_state(
        SimpleNamespace(data={"entity_id":"binary_sensor.rain"})
    )
    assert hass.calls == []
    assert circuit.running is True


@pytest.mark.asyncio
async def test_partial_start_must_be_explicitly_stopped_before_retry(circuit_class):
    hass = MockHass("off")
    circuit = make_circuit(circuit_class, hass)
    circuit._owned_valves = {"switch.test_valve"}
    circuit.weather = SimpleNamespace(
        update=lambda cfg: asyncio.sleep(0), rain_blocked=False
    )
    circuit.calculation = lambda: SimpleNamespace(seconds=30)
    circuit.config = {"valves":["switch.test_valve"],"base_seconds":30,"max_runtime":60}
    with pytest.raises(RuntimeError,match="previous_start_requires_explicit_stop"):
        await circuit.start(manual=True)
    assert hass.calls == []


@pytest.mark.asyncio
async def test_setup_with_externally_active_valve_never_sends_off(circuit_class):
    hass = MockHass("on")
    hass.async_create_task = lambda task: task.close()
    circuit = make_circuit(circuit_class, hass)
    circuit.store = SimpleNamespace(
        async_load=lambda: asyncio.sleep(0, result={
            "config": {
                "automatic": False,
                "weather_entity": None,
                "rain_sensor": None,
                "precipitation_sensor": None,
                "precipitation_sensor_kind": "total",
                "valves": ["switch.test_valve"],
                "base_seconds": 30,
                "max_rain_today": 2,
                "max_rain_3d": 2,
                "min_temp": 23,
                "max_temp": 35,
                "max_runtime": 3600,
                "weekdays": [0, 1, 2, 3, 4, 5],
                "months": [4, 5, 6, 7, 8, 9, 10],
                "start_time": "08:00",
                "start_mode": "time",
                "predecessor": None,
            },
            "running": True,
        })
    )
    circuit.weather = SimpleNamespace(
        setup=lambda: asyncio.sleep(0), update=lambda cfg: asyncio.sleep(0)
    )
    circuit._listen = lambda: None
    await circuit.setup()
    assert hass.calls == []
    assert circuit.running is False
    assert circuit.status == "stopped"



@pytest.mark.asyncio
async def test_change_start_time_preserves_actual_watered_marker(circuit_class):
    from zoneinfo import ZoneInfo
    sys.modules["homeassistant.util.dt"].now = lambda: datetime(
        2026, 11, 16, 14, 14, tzinfo=ZoneInfo("Europe/Berlin")
    )
    circuit = make_circuit(circuit_class, MockHass("off"))
    defaults = sys.modules["wetsoil_off_test.const"].defaults
    circuit.config = defaults()
    circuit.config["start_time"] = "07:00"
    circuit.config["months"] = [11]
    circuit.last_auto_run_date = "2026-11-16"
    circuit.last_slot = "2026-11-16@07:00"
    circuit._listen = lambda: None
    circuit.weather = SimpleNamespace(update=lambda cfg: asyncio.sleep(0))
    await circuit.update_config({**circuit.config, "start_time": "15:00"})
    assert circuit.last_auto_run_date == "2026-11-16"
    assert circuit.last_slot == "2026-11-16@07:00"
    # A previously skipped 07:00 slot, however, never set auto run date,
    # hence a newly configured 15:00 slot remains eligible.
    circuit.last_auto_run_date = None
    assert circuit.last_auto_run_date is None


@pytest.mark.asyncio
async def test_failed_config_save_keeps_slot_and_watered_marker(circuit_class):
    circuit = make_circuit(circuit_class, MockHass("off"))
    defaults = sys.modules["wetsoil_off_test.const"].defaults
    circuit.config = defaults()
    circuit.config["start_time"] = "07:00"
    circuit.last_slot = "2026-11-16@07:00"
    circuit.last_auto_run_date = "2026-11-16"
    before = dict(circuit.config)

    async def fail_persist():
        raise RuntimeError("storage failure")
    circuit._save = fail_persist
    with pytest.raises(RuntimeError, match="storage failure"):
        await circuit.update_config({**circuit.config, "start_time": "15:00"})
    assert circuit.config == before
    assert circuit.last_slot == "2026-11-16@07:00"
    assert circuit.last_auto_run_date == "2026-11-16"


@pytest.mark.asyncio
async def test_runtime_snapshot_uses_configured_ha_timezone(circuit_class):
    from zoneinfo import ZoneInfo
    from types import SimpleNamespace
    dt=sys.modules["homeassistant.util.dt"]
    dt.utcnow=lambda: datetime(2026,11,16,13,30,tzinfo=timezone.utc)
    hass=MockHass("off")
    hass.config=SimpleNamespace(time_zone="Europe/Berlin")
    circuit=make_circuit(circuit_class,hass)
    defaults=sys.modules["wetsoil_off_test.const"].defaults
    circuit.config=defaults()
    circuit.config["start_time"]="16:00"
    circuit.config["months"]=[11]
    circuit.last_attempt=None
    circuit.entry=SimpleNamespace(entry_id="test",title="Test 1",data={"area_id":None})
    circuit.started = None
    circuit.calculation=lambda: SimpleNamespace(
        seconds=0,reason="incomplete",temp_factor=None,
        rain_today_factor=None,rain_3d_factor=None
    )
    circuit.weather=SimpleNamespace(
        rain_source_disagreement=False,rain_today=None,rain_3d=None,
        temperature=None,raining=None,weather_raining=None,
        sensor_raining=None,quality="incomplete",forecast_source=None,
        forecast_entity=None,forecast_updated=None,forecast_error=None,
        history=SimpleNamespace(days={},provenance={}),
        history_error="not_checked",intensity_total_72h=None
    )
    value=circuit.snapshot()
    assert value["next_start"].startswith("2026-11-16T16:00")
    assert value["schedule_today"]=="today_allowed"
    assert value["schedule_local_now"].startswith("2026-11-16T14:30")
    assert value["schedule_time_zone"]=="Europe/Berlin"


@pytest.mark.asyncio
async def test_disabled_automatic_attempt_does_not_consume_day(circuit_class):
    from zoneinfo import ZoneInfo
    dt=sys.modules["homeassistant.util.dt"]
    dt.utcnow=lambda: datetime(2026,11,16,6,0,tzinfo=timezone.utc)
    hass=MockHass("off")
    hass.config=SimpleNamespace(time_zone="Europe/Berlin")
    circuit=make_circuit(circuit_class,hass)
    cfg=sys.modules["wetsoil_off_test.const"].defaults()
    cfg.update({"automatic":False,"weather_entity":"weather.home",
                "valves":["switch.test_valve"],"months":[11]})
    circuit.config=cfg
    circuit.weather=SimpleNamespace(update=lambda cfg: asyncio.sleep(0),
                                    rain_blocked=False)
    circuit.planned=lambda: 0
    circuit.calculation=lambda: SimpleNamespace(reason="missing_history")
    await circuit.auto_attempt()
    assert circuit.last_auto_run_date is None
    assert circuit.last_started_date is None
    assert circuit.last_skip_reason == "automatic_disabled"
    assert hass.calls == []


@pytest.mark.asyncio
async def test_skipped_chain_can_attempt_again_after_weather_recovers(circuit_class):
    dt=sys.modules["homeassistant.util.dt"]
    dt.utcnow=lambda: datetime(2026,11,16,13,0,tzinfo=timezone.utc)
    hass=MockHass("off")
    hass.config=SimpleNamespace(time_zone="Europe/Berlin")
    circuit=make_circuit(circuit_class,hass)
    cfg=sys.modules["wetsoil_off_test.const"].defaults()
    cfg.update({"automatic":True,"start_mode":"chained","predecessor":"parent",
                "weather_entity":"weather.home","valves":["switch.test_valve"],
                "months":[11]})
    circuit.config=cfg
    circuit.weather=SimpleNamespace(update=lambda cfg: asyncio.sleep(0),
                                    rain_blocked=False)
    circuit.planned=lambda: 0
    circuit.calculation=lambda: SimpleNamespace(reason="missing_history")
    await circuit.auto_attempt()
    await circuit.auto_attempt()
    assert circuit.last_auto_run_date is None
    assert circuit.last_skip_reason == "missing_history"
    assert "Duplicate chain trigger blocked" not in circuit.events


@pytest.mark.asyncio
async def test_manual_reset_clears_today_without_operating_actuators(circuit_class):
    hass=MockHass("off")
    circuit=make_circuit(circuit_class,hass)
    circuit.last_started_date="2026-11-16"
    circuit.last_auto_run_date="2026-11-16"
    circuit.last_run_at="2026-11-16T07:00:00+00:00"
    circuit.last_slot="2026-11-16@07:00"
    await circuit.reset_today_status()
    assert circuit.last_started_date is None
    assert circuit.last_auto_run_date is None
    assert circuit.last_run_at=="2026-11-16T07:00:00+00:00"
    assert circuit.last_slot=="2026-11-16@07:00"
    assert hass.calls==[]


@pytest.mark.asyncio
async def test_reset_during_owned_run_rejected(circuit_class):
    hass=MockHass("on")
    circuit=make_circuit(circuit_class,hass)
    circuit.running=True
    circuit._owned_valves={"switch.test_valve"}
    with pytest.raises(ValueError,match="stop_before_reset_today"):
        await circuit.reset_today_status()
    assert hass.calls == []


@pytest.mark.asyncio
async def test_legacy_saved_attempt_not_treated_as_watered(circuit_class):
    hass=MockHass("off")
    hass.async_create_task=lambda coro:coro.close()
    circuit=make_circuit(circuit_class,hass)
    defaults=sys.modules["wetsoil_off_test.const"].defaults
    circuit.store=SimpleNamespace(
        async_load=lambda:asyncio.sleep(0,result={
            "config":defaults(), "last_attempt":"2026-11-16",
            "running":False
        })
    )
    circuit.weather=SimpleNamespace(setup=lambda:asyncio.sleep(0))
    circuit._listen=lambda:None
    await circuit.setup()
    assert circuit.last_auto_run_date is None
    assert circuit.last_started_date is None
    assert circuit.last_attempt is None


@pytest.mark.asyncio
async def test_confirmed_auto_start_marks_today_and_blocks_duplicate(circuit_class):
    from zoneinfo import ZoneInfo
    dt=sys.modules["homeassistant.util.dt"]
    dt.utcnow=lambda: datetime(2026,11,16,13,0,tzinfo=timezone.utc)
    hass=MockHass("off")
    hass.config=SimpleNamespace(time_zone="Europe/Berlin")
    hass.async_create_task=lambda task:(task.close() or None)
    async def set_on(h):
        if h.calls[-1][1] == "turn_on":
            h.values["switch.test_valve"]="on"
    hass.on_call=set_on
    circuit=make_circuit(circuit_class,hass)
    cfg=sys.modules["wetsoil_off_test.const"].defaults()
    cfg.update({"automatic":True,"months":[11],
                "weather_entity":"weather.home","valves":["switch.test_valve"]})
    circuit.config=cfg
    circuit.weather=SimpleNamespace(update=lambda cfg:asyncio.sleep(0),
                                    rain_blocked=False)
    circuit.planned=lambda:5
    captured=[]
    async def save_state():
        captured.append((circuit.last_started_date,circuit.last_auto_run_date,
                         circuit.last_run_at,circuit.last_run_kind))
    circuit._save=save_state
    await circuit.auto_attempt()
    assert circuit.running is True
    assert circuit.last_started_date == "2026-11-16"
    assert circuit.last_auto_run_date == "2026-11-16"
    assert circuit.last_run_kind == "auto"
    assert circuit.last_run_at is not None
    assert captured[-1][0:2] == ("2026-11-16","2026-11-16")
    before=len(hass.calls)
    await circuit.auto_attempt()
    assert len(hass.calls) == before
    assert circuit.last_skip_reason == "already_watered_today"


@pytest.mark.asyncio
async def test_manual_run_is_visible_but_does_not_consume_auto_day(circuit_class):
    from zoneinfo import ZoneInfo
    dt=sys.modules["homeassistant.util.dt"]
    dt.utcnow=lambda: datetime(2026,11,16,13,0,tzinfo=timezone.utc)
    hass=MockHass("off")
    hass.config=SimpleNamespace(time_zone="Europe/Berlin")
    hass.async_create_task=lambda task:(task.close() or None)
    async def set_on(h):
        if h.calls[-1][1] == "turn_on":
            h.values["switch.test_valve"]="on"
    hass.on_call=set_on
    circuit=make_circuit(circuit_class,hass)
    cfg=sys.modules["wetsoil_off_test.const"].defaults()
    cfg.update({"weather_entity":"weather.home","valves":["switch.test_valve"]})
    circuit.config=cfg
    circuit.weather=SimpleNamespace(update=lambda cfg:asyncio.sleep(0),
                                    rain_blocked=False)
    circuit.calculation=lambda:SimpleNamespace(seconds=5)
    await circuit.start(manual=True)
    assert circuit.last_started_date == "2026-11-16"
    assert circuit.last_auto_run_date is None
    assert circuit.last_run_kind == "manual"
