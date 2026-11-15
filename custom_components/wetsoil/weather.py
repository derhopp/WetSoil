"""Actual precipitation observation and safe weather forecast normalization."""
from __future__ import annotations

from datetime import date, datetime, timedelta, time
import logging
import math

from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)
RAIN_STATES = {"rainy", "pouring", "lightning-rainy", "snowy-rainy"}


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

    async def restore(self):
        data = await self.store.async_load() or {}
        self.days = data.get("days", {})
        self.current = data.get("current")
        self.last_sample = data.get("last_sample")

    async def save(self):
        await self.store.async_save({
            "days": self.days, "current": self.current,
            "last_sample": self.last_sample,
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
            else:
                self.days.pop(previous["day"], None)
            self.days = dict(sorted(self.days.items())[-10:])
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
        self.quality = "unavailable"
        self.last_fetch = None
        self.history = RainfallHistory(hass, entry_id)

    async def setup(self):
        await self.history.restore()

    def read_rain(self, settings):
        """Unknown sources never translate to no rain."""
        sources = []
        weather_id = settings["weather_entity"]
        sensor_id = settings["rain_sensor"]
        if weather_id:
            state = self.hass.states.get(weather_id)
            sources.append(
                None if state is None or state.state in ("unknown", "unavailable")
                else state.state in RAIN_STATES
            )
        if sensor_id:
            state = self.hass.states.get(sensor_id)
            sources.append(
                None if state is None or state.state not in ("on", "off")
                else state.state == "on"
            )
        self.raining = (True if True in sources
                        else False if sources and all(v is False for v in sources)
                        else None)
        return self.raining

    async def update(self, settings, force=False):
        """Refresh rain, observations and forecasts; never synthesize history."""
        now = dt_util.now()
        self.read_rain(settings)
        sensor_id = settings["precipitation_sensor"]
        if sensor_id:
            state = self.hass.states.get(sensor_id)
            amount = (as_mm(state.state, state.attributes.get("unit_of_measurement"))
                      if state is not None else None)
            await self.history.sample(now, amount, settings["precipitation_sensor_kind"])
        self.rain_3d = self.history.three_day_mean(now.date())
        if not settings["weather_entity"]:
            self.temperature = self.rain_today = None
            self.quality = "weather_unconfigured"
            return
        if (not force and self.last_fetch is not None
            and (now - self.last_fetch).total_seconds() < 1800):
            return
        # Record attempt to throttle failing providers as well.
        self.last_fetch = now
        self.temperature = self.rain_today = None
        entity_id = settings["weather_entity"]
        state = self.hass.states.get(entity_id)
        if state is None:
            self.quality = "weather_unavailable"
            return
        try:
            result = await self.hass.services.async_call(
                "weather", "get_forecasts",
                {"entity_id": entity_id, "type": "daily"},
                blocking=True, return_response=True,
            )
            rows = (result or {}).get(entity_id, {}).get("forecast", [])
            temp_unit = state.attributes.get("temperature_unit", "°C")
            rain_unit = state.attributes.get("precipitation_unit", "mm")
            self.temperature, self.rain_today = daily_forecast(
                rows, now.date(), rain_unit, temp_unit)
        except Exception:
            _LOGGER.exception("WetSoil: daily weather forecast failed for %s", entity_id)
        self.quality = ("ready" if
                        self.temperature is not None and self.rain_today is not None
                        and self.rain_3d is not None and self.raining is not None
                        else "incomplete")
