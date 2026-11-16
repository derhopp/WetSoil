"""WetSoil circuit runtime: manages only irrigation runs started by WetSoil."""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import timedelta
import logging

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .algorithm import calculate
from .const import DOMAIN, defaults, validate_config
from .weather import WetSoilWeather
from .schedule import local_occurrence, next_scheduled

_LOGGER = logging.getLogger(__name__)
EVENT = "wetsoil_updated"


class Circuit:
    """An independent circuit controlled by a single serialized runtime."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.store = Store(hass, 1, "wetsoil." + entry.entry_id)
        self.config = defaults()
        self.weather = WetSoilWeather(hass, entry.entry_id)
        self.lock = asyncio.Lock()
        self.running = False
        self.kind = None
        self.status = "idle"
        self.error = None
        self.started = None
        self.ended = None
        self.ends = None
        self.last_attempt = None
        self._owned_valves = set()
        self.events = deque(maxlen=30)
        self._task = None
        self._unsub = []
        self._closed = False

    def changed(self):
        self.hass.bus.async_fire(EVENT, {"entry_id": self.entry.entry_id})

    async def _save(self):
        await self.store.async_save({
            "config": self.config,
            "running": self.running,
            "last_attempt": self.last_attempt,
        })

    async def setup(self):
        saved = await self.store.async_load() or {}
        try:
            self.config = validate_config(saved.get("config", defaults()))
        except ValueError:
            _LOGGER.exception("WetSoil invalid stored config")
            self.config = defaults()
        self.last_attempt = saved.get("last_attempt")
        await self.weather.setup()
        # Do not touch actuators after restart, including an interrupted run.
        # The owner must provide independent fail-safe hardware/automation.
        if saved.get("running"):
            self.events.append("Interrupted run not resumed; external shutdown is the user's responsibility")
            self.status = "stopped"
        await self._save()
        self._listen()
        self.hass.async_create_task(self.weather.update(self.config))

    def _listen(self):
        self._unlisten()
        watched = set()
        for key in ("weather_entity", "rain_sensor", "precipitation_sensor"):
            if self.config[key]:
                watched.add(self.config[key])
        self._unsub.append(async_track_time_interval(
            self.hass, self._tick, timedelta(seconds=30)))
        if watched:
            self._unsub.append(async_track_state_change_event(
                self.hass, list(watched), self._state_event))

    def _unlisten(self):
        for cb in self._unsub:
            cb()
        self._unsub.clear()

    @callback
    def _state_event(self, event):
        """React immediately to rain or disconnected valves."""
        if not self._closed:
            self.hass.async_create_task(self._check_state(event))

    async def _check_state(self, event):
        self.weather.read_rain(self.config)
        # External actuator changes and rain transitions must never issue
        # unsolicited OFF commands. Start eligibility remains independent.
        if event.data.get("entity_id") == self.config["precipitation_sensor"]:
            # Sampling also occurs regularly to detect long data gaps.
            self.hass.async_create_task(self.weather.update(self.config))

    def calculation(self):
        w = self.weather
        c = self.config
        return calculate(
            c["base_seconds"], c["max_rain_today"], c["max_rain_3d"],
            c["min_temp"], c["max_temp"], w.rain_today, w.rain_3d,
            w.temperature, w.rain_blocked,
        )

    def planned(self):
        now = dt_util.now()
        c = self.config
        if not c["automatic"] or not c["valves"]:
            return 0
        if now.weekday() not in c["weekdays"] or now.month not in c["months"]:
            return 0
        result = self.calculation()
        return min(result.seconds, c["max_runtime"]) if result.seconds is not None else None

    def snapshot(self):
        calc = self.calculation()
        local = dt_util.now()
        next_time = next_scheduled(
            local, self.config["start_time"],
            self.config["weekdays"], self.config["months"]
        ) if self.config["start_mode"] == "time" else None
        return {
            "entry_id": self.entry.entry_id,
            "name": self.entry.title,
            "area_id": self.entry.data.get("area_id"),
            "config": self.config,
            "status": self.status,
            "error": self.error,
            "running": self.running,
            "kind": self.kind,
            "reason": (
                self.error or
                ("rain_sources_disagree" if self.weather.rain_source_disagreement
                 else calc.reason)
            ),
            "computed_seconds": calc.seconds,
            "planned_seconds": self.planned(),
            "remaining_seconds": max(0, (dt_util.parse_datetime(self.ends) - dt_util.utcnow()).total_seconds()) if self.ends else 0,
            "next_start": (
                next_time.isoformat() if next_time is not None
                else ("after:" + self.config["predecessor"]
                      if self.config["start_mode"] == "chained" else None)
            ),
            "started_at": self.started,
            "last_end": self.ended,
            "rain_today": self.weather.rain_today,
            "rain_3d": self.weather.rain_3d,
            "temperature": self.weather.temperature,
            "raining": self.weather.raining,
            "weather_raining": self.weather.weather_raining,
            "sensor_raining": self.weather.sensor_raining,
            "rain_source_disagreement": self.weather.rain_source_disagreement,
            "quality": self.weather.quality,
            "forecast_source": self.weather.forecast_source,
            "forecast_entity": self.weather.forecast_entity,
            "forecast_updated": self.weather.forecast_updated,
            "forecast_error": self.weather.forecast_error,
            "history_source": {
                day: self.weather.history.provenance.get(day, "observed")
                for day in self.weather.history.days
            },
            "history_status": self.weather.history_error,
            "intensity_total_72h": self.weather.intensity_total_72h,
            "factors": {"temp": calc.temp_factor,
                        "today": calc.rain_today_factor,
                        "history": calc.rain_3d_factor},
            "events": list(self.events),
        }

    async def update_config(self, settings):
        """Settings are persisted atomically without changing active valves."""
        new = validate_config(settings)
        previous = self.config
        reset_history = (
            new["precipitation_sensor"] != previous["precipitation_sensor"]
            or new["precipitation_sensor_kind"] != previous["precipitation_sensor_kind"]
        )
        if (self.running or self._owned_valves) and any(
            new[key] != previous[key] for key in new if key != "automatic"
        ):
            raise ValueError("stop_before_changing_safety_parameters")
        # Disabling the schedule does not terminate an already running cycle.
        # The user can explicitly stop that cycle.
        async with self.lock:
            self.config = new
            try:
                await self._save()
            except Exception:
                self.config = previous
                raise
        if reset_history:
            self.weather.history.days.clear()
            self.weather.history.provenance.clear()
            self.weather.history.last_backfill = None
            self.weather.intensity_last_fetch = None
            self.weather.intensity_sensor_id = None
            self.weather.intensity_total_72h = None
            self.weather.rain_3d = None
            self.weather.history_error = "not_checked"
            self.weather.history.recorder_status = "not_checked"
            self.weather.history.current = None
            self.weather.history.last_sample = None
            await self.weather.history.save()
            self.weather.last_fetch = None
        self._listen()
        await self.weather.update(self.config)
        self.changed()

    async def _tick(self, now):
        if self._closed:
            return
        local = dt_util.as_local(now)
        if local.minute % 5 == 0 and local.second < 30:
            await self.weather.update(self.config)
            self.changed()
        settings = self.config
        if (settings["start_mode"] == "time"
            and local_occurrence(local.date(), settings["start_time"], local.tzinfo) is None
            and self.last_attempt != local.date().isoformat()):
            self.last_attempt = local.date().isoformat()
            self.events.append("Nonexistent local start time: safely skipped")
            await self._save()
            self.changed()
        if (settings["start_mode"] == "time"
            and local.strftime("%H:%M") == settings["start_time"]
            and self.last_attempt != local.date().isoformat()):
            self.last_attempt = local.date().isoformat()
            await self._save()
            await self.auto_attempt()

    async def auto_attempt(self):
        """A skipped circuit forwards to its single successor."""
        if self._closed:
            return
        if self.config["start_mode"] == "chained":
            today = dt_util.now().date().isoformat()
            if self.last_attempt == today:
                self.events.append("Duplicate chain trigger blocked")
                self.changed()
                return
            self.last_attempt = today
            await self._save()
        if self.running:
            self.events.append("Automatic attempt skipped: already running")
            self.changed()
            return
        await self.weather.update(self.config)
        seconds = self.planned()
        if seconds is not None and seconds > 0:
            try:
                await self.start(manual=False)
            except (RuntimeError, ValueError) as exc:
                self.error = str(exc)
                self.status = "error"
                self.events.append("Automatic start failed: " + str(exc))
                self.changed()
            return
        self.events.append("Automatic watering skipped")
        self.changed()
        await self._successor()

    async def _successor(self):
        for circuit in self.hass.data.get(DOMAIN, {}).values():
            if (circuit.config["start_mode"] == "chained"
                and circuit.config["predecessor"] == self.entry.entry_id):
                await circuit.auto_attempt()
                break

    async def start(self, manual=False):
        """Validate rain, turn on all switches and confirm their HA states."""
        await self.weather.update(self.config)
        if self.weather.rain_blocked is not False:
            raise RuntimeError("rain_or_unknown")
        if not self.config["valves"]:
            raise RuntimeError("no_valves")
        if manual:
            computed = self.calculation().seconds
            seconds = computed if computed and computed > 0 else self.config["base_seconds"]
        else:
            seconds = self.planned()
            if seconds is None or seconds <= 0:
                raise RuntimeError("not_eligible")
        seconds = min(seconds, self.config["max_runtime"])
        async with self.lock:
            if self.running:
                raise RuntimeError("already_running")
            if self._owned_valves:
                raise RuntimeError("previous_start_requires_explicit_stop")
            for valve in self.config["valves"]:
                state = self.hass.states.get(valve)
                if state is None or state.state != "off":
                    raise RuntimeError("valve_not_off:" + valve)
            self.status = "starting"
            self._owned_valves.clear()
            try:
                for valve in self.config["valves"]:
                    # Track before issuing a potentially timing-out service call:
                    # explicit Stop must be able to address a partially started run.
                    self._owned_valves.add(valve)
                    await asyncio.wait_for(
                        self.hass.services.async_call(
                            "switch", "turn_on", {"entity_id": valve}, blocking=True),
                        timeout=10,
                    )
                for valve in self.config["valves"]:
                    state = self.hass.states.get(valve)
                    if state is None or state.state != "on":
                        raise RuntimeError("valve_on_unconfirmed:" + valve)
            except Exception as exc:
                self.error = "start_failed:" + str(exc)
                self.status = "error"
                self.events.append(
                    "Start failed; actuators may remain on. Use explicit Stop or external controls."
                )
                self.changed()
                raise RuntimeError(self.error) from exc
            now = dt_util.utcnow()
            self.running = True
            self.kind = "manual" if manual else "auto"
            self.started = now.isoformat()
            self.ends = (now + timedelta(seconds=seconds)).isoformat()
            self.status = "watering"
            self.error = None
            self.events.append("Watering started: " + str(seconds) + "s")
            await self._save()
            self._task = self.hass.async_create_task(self._complete(seconds))
        self.changed()

    async def _complete(self, seconds):
        try:
            await asyncio.sleep(seconds)
            await self.stop("complete")
        except asyncio.CancelledError:
            pass

    async def _off(self, valves):
        """One ordinary OFF command per valve owned by a WetSoil run.

        No safety retries, state polling, lockouts or background shutdowns.
        """
        errors = []
        for valve in valves:
            try:
                await asyncio.wait_for(
                    self.hass.services.async_call(
                        "switch", "turn_off", {"entity_id": valve}, blocking=True
                    ), timeout=10
                )
            except Exception as exc:
                _LOGGER.warning("WetSoil stop command failed for %s: %s", valve, exc)
                errors.append(valve)
        return errors

    async def stop(self, reason="manual_stop", abort=True):
        """End only a WetSoil-owned run. An idle stop cannot affect actuators."""
        async with self.lock:
            was_running, kind = self.running, self.kind
            owned = tuple(self._owned_valves)
            if not was_running and not owned:
                return
            self.running = False
            self.kind = None
            if self._task is not None and self._task is not asyncio.current_task():
                self._task.cancel()
            self._task = None
            self._owned_valves.clear()
            errors = await self._off(owned)
            self.ended = dt_util.utcnow().isoformat()
            self.ends = None
            self.status = "error" if errors else ("idle" if reason == "complete" else "stopped")
            self.error = ("stop_command_failed:" + ",".join(errors)) if errors else None
            self.events.append("WetSoil run stopped: " + reason)
            await self._save()
        self.changed()
        if not errors and was_running and kind == "auto" and reason == "complete":
            await self._successor()

    async def shutdown(self):
        """Release timers without ever altering actuator states during unload."""
        self._closed = True
        self._unlisten()
        async with self.lock:
            if self._task is not None:
                self._task.cancel()
                self._task = None
            if self.running or self._owned_valves:
                self.events.append(
                    "WetSoil unloaded; actuator state left unchanged. External safety required."
                )
            self.running = False
            self.kind = None
            self._owned_valves.clear()
            self.ends = None
            self.status = "stopped"
            await self._save()
        self.changed()
