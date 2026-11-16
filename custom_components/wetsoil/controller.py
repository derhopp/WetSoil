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
from .schedule import (
    configured_local_now, local_occurrence, next_scheduled,
    today_schedule_reason,
)

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
        self.last_attempt = None  # Legacy diagnostic, never used as completion.
        self.last_slot = None
        self.last_started_date = None
        self.last_auto_run_date = None
        self.last_run_at = None
        self.last_run_kind = None
        self.last_skip_at = None
        self.last_skip_reason = None
        self._automatic_lock = asyncio.Lock()
        self._owned_valves = set()
        self.events = deque(maxlen=30)
        self._task = None
        self._unsub = []
        self._closed = False

    def changed(self):
        self.hass.bus.async_fire(EVENT, {"entry_id": self.entry.entry_id})

    async def _save(self):
        await self.store.async_save({
            "schema_version": 2,
            "config": self.config,
            "running": self.running,
            "last_slot": self.last_slot,
            "last_started_date": self.last_started_date,
            "last_auto_run_date": self.last_auto_run_date,
            "last_run_at": self.last_run_at,
            "last_run_kind": self.last_run_kind,
            "last_skip_at": self.last_skip_at,
            "last_skip_reason": self.last_skip_reason,
        })

    async def setup(self):
        saved = await self.store.async_load() or {}
        try:
            if saved.get("schema_version", 1) > 2:
                raise ValueError("unsupported_future_storage_schema")
            stored = saved.get("config", defaults())
            if not isinstance(stored, dict):
                raise ValueError("stored_configuration_not_a_mapping")
            # Version 1 may lack parameters introduced in later releases.
            # Keep values the user supplied, fill only absent newer keys.
            # Unknown keys remain invalid instead of being silently dropped.
            self.config = validate_config({**defaults(), **stored})
        except ValueError:
            _LOGGER.exception("WetSoil invalid stored config")
            self.config = defaults()
        # Prior versions stored even SKIPPED attempts as last_attempt.
        # They must never be migrated into proof of an actual watering run.
        self.last_attempt = None
        self.last_slot = saved.get("last_slot")
        self.last_started_date = saved.get("last_started_date")
        self.last_auto_run_date = saved.get("last_auto_run_date")
        self.last_run_at = saved.get("last_run_at")
        self.last_run_kind = saved.get("last_run_kind")
        self.last_skip_at = saved.get("last_skip_at")
        self.last_skip_reason = saved.get("last_skip_reason")
        # A deleted config entry must never leave a dangling automatic chain.
        # Config entries are registered before individual circuit setup.
        manager = getattr(self.hass, "config_entries", None)
        if manager is not None and hasattr(manager, "async_entries"):
            known = {
                record.entry_id for record in manager.async_entries(DOMAIN)
            }
            if (self.config["start_mode"] == "chained"
                    and self.config["predecessor"] not in known):
                self.config = {
                    **self.config, "automatic": False,
                    "start_mode": "time", "predecessor": None,
                }
                self.events.append(
                    "Predecessor missing: automatic irrigation disabled"
                )
        await self.weather.setup()
        # Do not touch actuators after restart, including an interrupted run.
        # The owner must provide independent fail-safe hardware/automation.
        if saved.get("running"):
            self.events.append("Interrupted run not resumed; external shutdown is the user's responsibility")
            self.status = "stopped"
        await self._save()
        self._listen()
        self.hass.async_create_task(self._refresh_weather())

    async def _refresh_weather(self, force=False):
        """Refresh diagnostics after startup or provider recovery."""
        try:
            await self.weather.update(self.config, force=force)
        except Exception:
            _LOGGER.exception("WetSoil weather refresh failed for %s", self.entry.entry_id)
        finally:
            if not self._closed:
                self.changed()

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
        # Never switch actuators off due to an external state change.
        entity_id = event.data.get("entity_id")
        if entity_id == self.config["weather_entity"]:
            state = event.data.get("new_state")
            if (state is not None
                    and state.state not in ("unknown", "unavailable")
                    and self.weather.forecast_source is None):
                # A provider coming online after HA restart should not wait
                # for the previous failed-request cache to expire.
                await self._refresh_weather(force=True)
        elif entity_id == self.config["precipitation_sensor"]:
            self.hass.async_create_task(self._refresh_weather())

    def calculation(self):
        w = self.weather
        c = self.config
        return calculate(
            c["base_seconds"], c["max_rain_today"], c["max_rain_3d"],
            c["min_temp"], c["max_temp"], w.rain_today, w.rain_3d,
            w.temperature, w.rain_blocked,
        )

    def planned(self):
        now = configured_local_now(self.hass)
        c = self.config
        if not c["automatic"] or not c["valves"]:
            return 0
        if now.weekday() not in c["weekdays"] or now.month not in c["months"]:
            return 0
        result = self.calculation()
        return min(result.seconds, c["max_runtime"]) if result.seconds is not None else None

    def snapshot(self):
        calc = self.calculation()
        local = configured_local_now(self.hass)
        next_time = next_scheduled(
            local, self.config["start_time"],
            self.config["weekdays"], self.config["months"],
            self.last_auto_run_date,
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
            "schedule_today": today_schedule_reason(
                local, self.config, self.last_auto_run_date
            ),
            "watered_today": self.last_started_date == local.date().isoformat(),
            "automatic_watered_today": (
                self.last_auto_run_date == local.date().isoformat()
            ),
            "last_real_start": self.last_run_at,
            "last_real_start_kind": self.last_run_kind,
            "last_skip_at": self.last_skip_at,
            "last_skip_reason": self.last_skip_reason,
            "schedule_local_now": local.isoformat(),
            "schedule_time_zone": getattr(
                getattr(self.hass, "config", None), "time_zone", str(local.tzinfo)
            ),
            "started_at": self.started,
            "last_end": self.ended,
            "rain_today": round(self.weather.rain_today, 2) if self.weather.rain_today is not None else None,
            "rain_3d": round(self.weather.rain_3d, 2) if self.weather.rain_3d is not None else None,
            "temperature": round(self.weather.temperature, 1) if self.weather.temperature is not None else None,
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
            "intensity_total_72h": (round(self.weather.intensity_total_72h, 2)
                                    if self.weather.intensity_total_72h is not None else None),
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
        # A changed future HH:MM produces a new unique time slot. Earlier
        # skipped slots never consume the day's actual-run allowance.
        # A completed automatic start still requires explicit status reset
        # before a second automatic run on the same local date.
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
        local = configured_local_now(self.hass, now)
        standard_refresh = local.minute % 5 == 0 and local.second < 30
        forecast_retry = (
            self.config["weather_entity"]
            and self.weather.forecast_source is None
            and (
                self.weather.last_fetch is None
                or (now - self.weather.last_fetch).total_seconds() >= 60
            )
        )
        if standard_refresh or forecast_retry:
            await self._refresh_weather()
        settings = self.config
        if settings["start_mode"] != "time":
            return
        if local.weekday() not in settings["weekdays"] or local.month not in settings["months"]:
            return
        slot = local.date().isoformat() + "@" + settings["start_time"]
        occurrence = local_occurrence(
            local.date(), settings["start_time"], local.tzinfo
        )
        if occurrence is None:
            if self.last_slot != slot:
                self.last_slot = slot
                self.events.append("Nonexistent local start time: skipped")
                await self._save()
                self.changed()
            return
        if local.strftime("%H:%M") == settings["start_time"] and self.last_slot != slot:
            # Avoid retry storms during the same minute, without ever turning
            # skipped attempts into a completed watering marker.
            self.last_slot = slot
            await self._save()
            await self.auto_attempt()

    def _record_skip(self, reason):
        self.last_skip_at = dt_util.utcnow().isoformat()
        self.last_skip_reason = str(reason)
        self.events.append("Automatic watering skipped: " + str(reason))

    async def auto_attempt(self):
        """Only an actual confirmed automatic start consumes today's run."""
        if self._closed:
            return
        async with self._automatic_lock:
            local_day = configured_local_now(self.hass).date().isoformat()
            if self.last_auto_run_date == local_day:
                self._record_skip("already_watered_today")
                await self._save()
                self.changed()
                return

            if self.running or self._owned_valves:
                self._record_skip("already_running")
                await self._save()
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
                    self._record_skip(str(exc))
                    await self._save()
                    self.changed()
                return

            if not self.config["automatic"]:
                reason = "automatic_disabled"
            elif not self.config["valves"]:
                reason = "no_valves"
            elif (configured_local_now(self.hass).weekday() not in self.config["weekdays"]
                  or configured_local_now(self.hass).month not in self.config["months"]):
                reason = "calendar_excluded"
            else:
                reason = self.calculation().reason or "not_eligible"
            self._record_skip(reason)
            await self._save()
            self.changed()
            # Preserve prior chain semantics: skipped circles forward their
            # chain, but the next valid trigger can try them again.
            await self._successor()

    async def _successor(self):
        for circuit in self.hass.data.get(DOMAIN, {}).values():
            if (circuit.config["start_mode"] == "chained"
                and circuit.config["predecessor"] == self.entry.entry_id):
                await circuit.auto_attempt()
                break

    async def reset_today_status(self):
        """Admin-only explicit reset; never touches switches or schedules now."""
        async with self.lock:
            if self.running or self._owned_valves:
                raise ValueError("stop_before_reset_today")
            self.last_started_date = None
            self.last_auto_run_date = None
            # Retain last_run_at, last_skip and slot for diagnostics. A reset
            # cannot cause a repeat trigger within the current HH:MM minute.
            self.events.append("Today's watering markers reset by administrator")
            await self._save()
        self.changed()

    async def start(self, manual=False):
        """Issue ON once, then run the timer without waiting for ON feedback."""
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
                # Successful service return is sufficient to start the timer.
                # Switch state feedback can lag; it is not an ON handshake.
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
            self.last_run_at = self.started
            self.last_run_kind = self.kind
            local_day = configured_local_now(self.hass).date().isoformat()
            self.last_started_date = local_day
            if not manual:
                self.last_auto_run_date = local_day
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
