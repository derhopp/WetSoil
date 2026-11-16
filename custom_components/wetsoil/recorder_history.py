"""Conservative Recorder backfill of measured precipitation.

Recorder stores state changes, not guaranteed periodic samples. A day is accepted
only when it contains enough timestamped observations to independently establish
coverage; unchanged/sparse sensors correctly remain unavailable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, time, timezone
import logging

_LOGGER = logging.getLogger(__name__)


def aggregate_days(states, today, tz, kind, to_mm):
    """Validate and reconstruct exactly the three prior local calendar days.

    A reset, gap, invalid unit, missing start/end bracket or DST discontinuity
    invalidates the entire day. No forecast values ever enter the aggregation.
    """
    results = {}
    for offset in (3, 2, 1):
        day = today - timedelta(days=offset)
        begin = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc)
        end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc)
        points = []
        for state in states:
            stamp = getattr(state, "last_updated", None)
            if not isinstance(stamp, datetime) or stamp.tzinfo is None:
                continue
            stamp = stamp.astimezone(timezone.utc)
            if begin <= stamp < end:
                raw = getattr(state, "state", None)
                attributes = getattr(state, "attributes", {}) or {}
                unit = attributes.get("unit_of_measurement")
                value = to_mm(raw, unit)
                if value is None:
                    points = []
                    break
                points.append((stamp, value, unit))
        if not points:
            continue
        points.sort(key=lambda point: point[0])
        duration = (end - begin).total_seconds()
        if (len(points) < int((duration / 300) * 0.95)
                or (points[0][0] - begin).total_seconds() > 900
                or (end - points[-1][0]).total_seconds() > 900):
            continue
        units = {point[2] for point in points}
        if len(units) != 1:
            continue
        if any(
            (second[0] - first[0]).total_seconds() <= 0
            or (second[0] - first[0]).total_seconds() > 900
            or second[1] < first[1]
            for first, second in zip(points, points[1:])
        ):
            continue
        if kind == "daily":
            amount = points[-1][1]
        elif kind == "total":
            amount = points[-1][1] - points[0][1]
        else:
            continue
        if amount >= 0:
            results[day.isoformat()] = round(amount, 5)
    return results


async def read_recorder(hass, entity_id, today, tz, kind, to_mm):
    """Query Recorder off the event loop. Return (days, diagnostic status)."""
    if "recorder" not in hass.config.components:
        return {}, "recorder_not_loaded"
    try:
        from homeassistant.components.recorder import is_entity_recorded
        from homeassistant.components.recorder.history import get_significant_states

        if not is_entity_recorded(hass, entity_id):
            return {}, "recorder_entity_excluded"
        start = datetime.combine(
            today - timedelta(days=3), time.min, tzinfo=tz
        ).astimezone(timezone.utc)
        end = datetime.combine(today, time.min, tzinfo=tz).astimezone(timezone.utc)
        rows = await hass.async_add_executor_job(
            get_significant_states, hass, start, end, [entity_id],
            None, False, False, False, False, False
        )
        states = rows.get(entity_id, [])
        days = aggregate_days(states, today, tz, kind, to_mm)
        return days, "recorder_complete" if len(days) == 3 else "recorder_incomplete"
    except Exception:
        _LOGGER.exception("WetSoil: Recorder backfill failed for %s", entity_id)
        return {}, "recorder_error"


INTENSITY_WINDOW = timedelta(hours=72)


def intensity_mm_per_hour(value, unit):
    """Return a finite nonnegative precipitation rate in millimetres per hour."""
    import math
    try:
        rate = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if not math.isfinite(rate) or rate < 0:
        return None
    factors = {
        "mm/h": 1.0, "mm/hr": 1.0, "mm/d": 1 / 24, "mm/day": 1 / 24,
        "in/h": 25.4, "in/hr": 25.4, "in/d": 25.4 / 24, "in/day": 25.4 / 24,
        "cm/h": 10.0, "cm/d": 10.0 / 24,
    }
    scale = factors.get(unit)
    return rate * scale if scale is not None else None


def integrate_intensity(states, start, end):
    """Integrate recorder rate states in a rolling 72-hour UTC window.

    The initial state must be known at or before the left boundary.
    Recorder contains changes, not regular samples: a stable zero is valid
    regardless of the number of changes. Unknown state intervals invalidate
    the entire window rather than being silently treated as dry.
    """
    if start.tzinfo is None or end.tzinfo is None or end - start != INTENSITY_WINDOW:
        return None
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    points = []
    for state in states:
        timestamp = getattr(state, "last_updated", None)
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            return None
        stamp = timestamp.astimezone(timezone.utc)
        if stamp > end:
            continue
        attrs = getattr(state, "attributes", {}) or {}
        value = intensity_mm_per_hour(getattr(state, "state", None),
                                      attrs.get("unit_of_measurement"))
        points.append((stamp, value))
    points.sort(key=lambda point: point[0])
    initial = [v for t, v in points if t <= start]
    if not initial or initial[-1] is None:
        return None
    previous = start
    rate = initial[-1]
    total = 0.0
    for stamp, next_rate in points:
        if stamp <= start:
            continue
        if stamp <= previous or next_rate is None:
            return None
        total += rate * (stamp - previous).total_seconds() / 3600
        previous, rate = stamp, next_rate
    total += rate * (end - previous).total_seconds() / 3600
    return round(total, 5)


async def read_intensity_recorder(hass, entity_id, now):
    """Read the last 72 hours of real rain intensity, or return unavailable."""
    if "recorder" not in hass.config.components:
        return None, "recorder_not_loaded"
    current = hass.states.get(entity_id)
    if current is None or intensity_mm_per_hour(
        current.state, current.attributes.get("unit_of_measurement")
    ) is None:
        return None, "intensity_sensor_unavailable"
    try:
        from homeassistant.components.recorder import is_entity_recorded
        from homeassistant.components.recorder.history import get_significant_states

        if not is_entity_recorded(hass, entity_id):
            return None, "recorder_entity_excluded"
        end = now.astimezone(timezone.utc)
        start = end - INTENSITY_WINDOW
        rows = await hass.async_add_executor_job(
            get_significant_states, hass, start, end, [entity_id],
            None, True, False, False, False, False
        )
        amount = integrate_intensity(rows.get(entity_id, []), start, end)
        return (amount, "intensity_72h_complete") if amount is not None else (
            None, "intensity_72h_incomplete"
        )
    except Exception:
        _LOGGER.exception("WetSoil Recorder intensity retrieval failed for %s", entity_id)
        return None, "recorder_error"
