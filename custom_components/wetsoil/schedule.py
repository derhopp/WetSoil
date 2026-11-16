"""Pure timezone-aware scheduling helpers with DST safeguards."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_occurrence(day, hhmm, tz):
    """Return first local occurrence; nonexistent spring-forward times are None."""
    hours, minutes = map(int, hhmm.split(":"))
    local = datetime(day.year, day.month, day.day,
                     hours, minutes, tzinfo=tz, fold=0)
    round_trip = local.astimezone(timezone.utc).astimezone(tz)
    if round_trip.replace(tzinfo=None) != local.replace(tzinfo=None):
        return None
    return local


def configured_local_now(hass, utc_now=None):
    """Use HA's explicitly configured zone, independent of process timezone."""
    from homeassistant.util import dt as dt_util
    configured_zone = getattr(getattr(hass, "config", None), "time_zone", None)
    if configured_zone:
        try:
            instant = utc_now if utc_now is not None else dt_util.utcnow()
            return instant.astimezone(ZoneInfo(configured_zone))
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            pass
    # Backwards-compatible fallback for stripped-down HA test doubles.
    return dt_util.as_local(utc_now) if utc_now is not None else dt_util.now()


def today_schedule_reason(now, settings, last_attempt=None):
    """Explain today's eligibility without silently overriding calendar filters."""
    if settings["start_mode"] != "time":
        return "chained"
    if now.month not in settings["months"]:
        return "month_excluded"
    if now.weekday() not in settings["weekdays"]:
        return "weekday_excluded"
    scheduled = local_occurrence(now.date(), settings["start_time"], now.tzinfo)
    if scheduled is None:
        return "time_nonexistent"
    if (scheduled.astimezone(timezone.utc)
            <= now.astimezone(timezone.utc)):
        return "time_passed"
    if last_attempt == now.date().isoformat():
        return "already_attempted"
    return "today_allowed"


def next_scheduled(now, hhmm, weekdays, months, last_attempt=None):
    """Return next allowed local start or None if there is no matching day.

    Ambiguous fall-back times intentionally use the first occurrence.
    """
    for offset in range(370):
        day = (now + timedelta(days=offset)).date()
        if (day.weekday() not in weekdays or day.month not in months
                or day.isoformat() == last_attempt):
            continue
        candidate = local_occurrence(day, hhmm, now.tzinfo)
        if (candidate is not None
                and candidate.astimezone(timezone.utc) >
                now.astimezone(timezone.utc)):
            return candidate
    return None


def should_rearm_today(previous, updated, last_attempt, now):
    """Re-arm one explicit future time change, not unrelated configuration edits.

    The persisted last_attempt is date-scoped for duplicate protection. A
    deliberate later start-time change creates a new upcoming occurrence,
    provided the new schedule allows today.
    """
    day = now.date()
    if (
        previous["start_mode"] != "time"
        or updated["start_mode"] != "time"
        or previous["start_time"] == updated["start_time"]
        or last_attempt != day.isoformat()
        or day.weekday() not in updated["weekdays"]
        or day.month not in updated["months"]
    ):
        return False
    occurrence = local_occurrence(day, updated["start_time"], now.tzinfo)
    return (occurrence is not None and
            occurrence.astimezone(timezone.utc) >
            now.astimezone(timezone.utc))
