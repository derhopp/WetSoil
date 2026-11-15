"""Pure timezone-aware scheduling helpers with DST safeguards."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def local_occurrence(day, hhmm, tz):
    """Return first local occurrence; nonexistent spring-forward times are None."""
    hours, minutes = map(int, hhmm.split(":"))
    local = datetime(day.year, day.month, day.day,
                     hours, minutes, tzinfo=tz, fold=0)
    round_trip = local.astimezone(timezone.utc).astimezone(tz)
    if round_trip.replace(tzinfo=None) != local.replace(tzinfo=None):
        return None
    return local


def next_scheduled(now, hhmm, weekdays, months):
    """Return next allowed local start or None if there is no matching day.

    Ambiguous fall-back times intentionally use the first occurrence.
    """
    for offset in range(370):
        day = (now + timedelta(days=offset)).date()
        if day.weekday() not in weekdays or day.month not in months:
            continue
        candidate = local_occurrence(day, hhmm, now.tzinfo)
        if candidate is not None and candidate > now:
            return candidate
    return None
