"""Actual precipitation observation and safe weather forecast normalization."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, time, timezone
import logging
import math

from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)
RAIN_STATES = {"rainy", "pouring", "lightning-rainy", "snowy-rainy", "snowy", "hail"}
DRY_STATES = {"clear-night", "sunny", "partlycloudy", "cloudy", "fog",
              "windy", "windy-variant"}


def as_number(raw):
    """Finite numeric sensor value, but not boolean."""
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def as_mm(value, unit):
    """Convert supported precipitation unit to millimetres."""
    amount = as_number(value)
    if amount is None or amount < 0:
        return None
    if unit in ("mm", "millimeter", "millimeters"):
        return amount
    if unit in ("in", "inch", "inches"):
        return amount * 25.4
    if unit in ("cm",):
        return amount * 10
    return None


def as_celsius(value, unit):
    """Convert supported temperature units to Celsius."""
    degree = as_number(value)
    if degree is None:
        return None
    if unit in ("°C", "C"):
        return degree
    if unit in ("°F", "F"):
        return (degree - 32) * 5 / 9
    return None


def daily_forecast(forecasts, local_date, precipitation_unit, temperature_unit):
    """Use the full daily forecast value matching the local calendar day."""
    for row in forecasts:
        text = row.get("datetime")
        if not isinstance(text, str):
            continue
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
            forecast_date = (dt_util.as_local(moment).date()
                             if moment.tzinfo else moment.date())
        except (ValueError, TypeError):
            continue
        if forecast_date != local_date:
            continue
        return (
            as_celsius(row.get("temperature"), temperature_unit),
            as_mm(row.get("precipitation"), precipitation_unit),
        )
    return None, None



def hourly_forecast(forecasts, local_date, precipitation_unit, temperature_unit, tz):
    """Calculate a complete local day's forecast, including DST's 23/25 hours.

    Never treat remaining-day hourly forecasts as complete-day precipitation.
    """
    start = datetime.combine(local_date, time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc)
    rows_by_hour = {}
    for row in forecasts:
        if not isinstance(row, dict):
            continue
        value = row.get("datetime")
        if not isinstance(value, str):
            continue
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if moment.tzinfo is None:
            continue
        utc = moment.astimezone(timezone.utc)
        if start <= utc < end:
            if utc in rows_by_hour:
                return None, None
            rows_by_hour[utc] = row

    temps, rain = [], []
    expected = start
    while expected < end:
        row = rows_by_hour.get(expected)
        if row is None:
            return None, None
        temp = as_celsius(row.get("temperature"), temperature_unit)
        mm = as_mm(row.get("precipitation"), precipitation_unit)
        if temp is None or mm is None:
            return None, None
        temps.append(temp)
        rain.append(mm)
        expected += timedelta(hours=1)
    return (max(temps), sum(rain)) if temps else (None, None)


class RainfallHistory:
    """Conservatively aggregate measured daily totals or cumulative counters.

    Samples are taken at approximately five-minute intervals. A day is only
    considered complete if its measurement coverage is at least 95%, including
    a measurement near the end of the day. Forecasts never enter this store.
    """

    def __init__(self, hass, entry_id):
        self.hass = hass
        self.store = Store(hass, 1, f"wetsoil_rain.{entry_id}")
        self.days = {}
        self.current = None
        self.last_sample = None
        self.provenance = {}
        self.recorder_status = "not_checked"
        self.last_backfill = None

    async def restore(self):
        data = await self.store.async_load() or {}
        self.days = data.get("days", {})
        self.current = data.get("current")
        self.last_sample = data.get("last_sample")
        self.provenance = data.get("provenance", {})

    async def save(self):
        await self.store.async_save({
            "days": self.days, "current": self.current,
            "last_sample": self.last_sample, "provenance": self.provenance,
        })

    async def sample(self, when, value, kind):
        """Ingest a real measurement; fail closed on resets and data gaps."""
        local_day = when.date().isoformat()
        stamp = when.isoformat()
        if value is None:
            if self.current:
                self.current["valid"] = False
                await self.save()
            return
        if self.current and self.current["day"] != local_day:
            previous = self.current
            # Samples should bracket midnight; the previous day must have
            # regular coverage and a valid end-of-day observation.
            try:
                last = datetime.fromisoformat(previous["last"])
                timely = (datetime.combine(when.date(), time.min, tzinfo=when.tzinfo)
                          - last).total_seconds() <= 900
            except (ValueError, KeyError):
                timely = False
            if previous["valid"] and previous["samples"] >= 274 and timely:
                self.days[previous["day"]] = round(previous["amount"], 5)
                self.provenance[previous["day"]] = "observed"
            else:
                self.days.pop(previous["day"], None)
                self.provenance.pop(previous["day"], None)
            self.days = dict(sorted(self.days.items())[-10:])
            self.provenance = {k: v for k, v in self.provenance.items()
                               if k in self.days}
            self.current = None
            self.last_sample = None
        if self.current is None:
            self.current = {"day": local_day, "amount": 0.0,
                            "last": stamp, "samples": 1, "valid": True}
            self.last_sample = value
            await self.save()
            return
        current = self.current
        last = datetime.fromisoformat(current["last"])
        elapsed = (when - last).total_seconds()
        if elapsed < 240:
            # Avoid counting multiple repeated sensor changes as independent
            # coverage samples. Incorporate values, but not sample count.
            counted = False
        else:
            counted = True
            if elapsed > 900:
                current["valid"] = False
            current["samples"] += 1
        if kind == "daily":
            if value < self.last_sample:
                current["valid"] = False
            current["amount"] = value
        elif kind == "total":
            delta = value - self.last_sample
            if delta < 0:
                current["valid"] = False
            else:
                current["amount"] += delta
        else:
            current["valid"] = False
        self.last_sample = value
        if counted:
            current["last"] = stamp
        await self.save()

    async def backfill(self, entity_id, kind, today, tz):
        """Merge only validated Recorder history; never overwrite local days."""
        from .recorder_history import read_recorder
        days, status = await read_recorder(
            self.hass, entity_id, today, tz, kind, as_mm
        )
        self.recorder_status = status
        added = False
        for day, amount in days.items():
            if day not in self.days:
                self.days[day] = amount
                self.provenance[day] = "recorder"
                added = True
        if added:
            self.days = dict(sorted(self.days.items())[-10:])
            await self.save()


    def three_day_mean(self, today):
        """Return None unless the three preceding local days are complete."""
        values = [
            self.days.get((today - timedelta(days=offset)).isoformat())
            for offset in (1, 2, 3)
        ]
        return sum(values) / 3 if all(v is not None for v in values) else None


class WetSoilWeather:
    """Weather fetch with provider rate-limit protection and conservative rain."""

    def __init__(self, hass, entry_id):
        self.hass = hass
        self.entry_id = entry_id
        self.temperature = None
        self.rain_today = None
        self.rain_3d = None
        self.raining = None
        self.rain_blocked = None
        self.rain_source_disagreement = False
        self.weather_raining = None
        self.sensor_raining = None
        self.quality = "unavailable"
        self.last_fetch = None
        self.forecast_entity = None
        self.forecast_date = None
        self.forecast_source = None
        self.forecast_updated = None
        self.forecast_error = None
        self._fetch_lock = asyncio.Lock()
        self.history = RainfallHistory(hass, entry_id)
        self.history_error = "not_checked"

    async def setup(self):
        await self.history.restore()

    def read_rain(self, settings):
        """Report observed rain separately from the conservative safety veto.

        An available dedicated rain sensor controls the displayed observation.
        Conflicting weather conditions still inhibit watering until resolved.
        """
        weather_id = settings["weather_entity"]
        sensor_id = settings["rain_sensor"]
        weather_raining = None
        sensor_raining = None
        if weather_id:
            state = self.hass.states.get(weather_id)
            if state and state.state in RAIN_STATES:
                weather_raining = True
            elif state and state.state in DRY_STATES:
                weather_raining = False
        if sensor_id:
            state = self.hass.states.get(sensor_id)
            if state and state.state in ("on", "off"):
                sensor_raining = state.state == "on"

        self.weather_raining = weather_raining
        self.sensor_raining = sensor_raining
        self.raining = sensor_raining if sensor_id else weather_raining
        self.rain_source_disagreement = (
            bool(sensor_id and weather_id)
            and sensor_raining is not None and weather_raining is not None
            and sensor_raining != weather_raining
        )
        if self.rain_source_disagreement:
            self.rain_blocked = None
        elif sensor_id and sensor_raining is None:
            self.rain_blocked = None
        elif weather_id and weather_raining is None:
            self.rain_blocked = None
        elif sensor_raining is True or weather_raining is True:
            self.rain_blocked = True
        elif sensor_raining is False or weather_raining is False:
            self.rain_blocked = False
        else:
            self.rain_blocked = None
        return self.raining

    async def update(self, settings, force=False):
        """Refresh observations and forecast, immediately when source changes."""
        async with self._fetch_lock:
            now = dt_util.now()
            today = dt_util.as_local(now).date()
            self.read_rain(settings)
            sensor_id = settings["precipitation_sensor"]
            amount = None
            if sensor_id:
                state = self.hass.states.get(sensor_id)
                amount = (as_mm(state.state, state.attributes.get("unit_of_measurement"))
                          if state is not None else None)
                await self.history.sample(dt_util.as_local(now), amount,
                                          settings["precipitation_sensor_kind"])
            if sensor_id and (
                self.history.three_day_mean(today) is None
                and (self.history.last_backfill is None
                     or (now - self.history.last_backfill).total_seconds() >= 21600)
            ):
                self.history.last_backfill = now
                tz = dt_util.as_local(now).tzinfo
                await self.history.backfill(
                    sensor_id, settings["precipitation_sensor_kind"], today, tz
                )
            self.rain_3d = (
                self.history.three_day_mean(today)
                if sensor_id and amount is not None else None
            )
            self.history_error = (
                "complete" if self.rain_3d is not None
                else self.history.recorder_status
            )
            entity_id = settings["weather_entity"]
            changed = entity_id != self.forecast_entity or today != self.forecast_date
            if changed:
                # Never show values from a formerly selected Weather Entity.
                self.forecast_entity = entity_id
                self.forecast_date = today
                self.last_fetch = None
                self.temperature = self.rain_today = None
                self.forecast_source = self.forecast_updated = None
                self.forecast_error = None
                self.quality = "weather_updating"
            if not entity_id:
                self.temperature = self.rain_today = None
                self.quality = "weather_unconfigured"
                self.forecast_error = "weather_unconfigured"
                return
            if (not force and self.last_fetch is not None
                    and (now - self.last_fetch).total_seconds() < 1800):
                self._update_quality()
                return
            self.last_fetch = now
            self.temperature = self.rain_today = None
            self.forecast_source = self.forecast_updated = None
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                self.forecast_error = "weather_unavailable"
                self._update_quality()
                return
            temp_unit = state.attributes.get("temperature_unit", "°C")
            rain_unit = state.attributes.get("precipitation_unit", "mm")
            errors = []
            # Preferred source: a *complete* hourly forecast for the local day.
            # Most providers omit past hours; then the daily forecast is safer.
            for kind in ("hourly", "daily"):
                try:
                    response = await self.hass.services.async_call(
                        "weather", "get_forecasts",
                        {"entity_id": entity_id, "type": kind},
                        blocking=True, return_response=True,
                    )
                    rows = (response or {}).get(entity_id, {}).get("forecast", [])
                    if not isinstance(rows, list):
                        rows = []
                    if kind == "hourly":
                        temp, precipitation = hourly_forecast(
                            rows, today, rain_unit, temp_unit,
                            dt_util.as_local(now).tzinfo,
                        )
                    else:
                        temp, precipitation = daily_forecast(
                            rows, today, rain_unit, temp_unit)
                    if temp is not None and precipitation is not None:
                        self.temperature, self.rain_today = temp, precipitation
                        self.forecast_source = kind
                        self.forecast_updated = now.isoformat()
                        self.forecast_error = None
                        break
                    errors.append(kind + "_incomplete")
                except Exception as exc:
                    _LOGGER.debug("WetSoil: %s forecast not supported for %s: %s",
                                  kind, entity_id, exc)
                    errors.append(kind + "_unavailable")
            if self.forecast_source is None:
                self.forecast_error = ",".join(errors) or "forecast_unavailable"
            self._update_quality()

    def _update_quality(self):
        """Treat missing forecast, history and rain consent as incomplete."""
        if self.forecast_entity is None:
            self.quality = "weather_unconfigured"
        elif self.temperature is None or self.rain_today is None:
            self.quality = "forecast_incomplete"
        elif self.rain_3d is None or self.rain_blocked is not False:
            self.quality = "incomplete"
        else:
            self.quality = "ready"
