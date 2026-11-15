"""Berlin DST and calendar tests for absolute and chained scheduling."""
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo
import importlib.util

PATH = Path(__file__).resolve().parents[1] / "custom_components/wetsoil/schedule.py"
spec = importlib.util.spec_from_file_location("wetsoil_schedule", PATH)
schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schedule)
BERLIN = ZoneInfo("Europe/Berlin")


def test_spring_forward_nonexistent_local_time():
    assert schedule.local_occurrence(date(2026, 3, 29), "02:30", BERLIN) is None
    now = datetime(2026, 3, 29, 0, 10, tzinfo=BERLIN)
    next_run = schedule.next_scheduled(now, "02:30", list(range(7)), list(range(1, 13)))
    assert next_run.date() == date(2026, 3, 30)


def test_fall_back_first_occurrence_only():
    planned = schedule.local_occurrence(date(2026, 10, 25), "02:30", BERLIN)
    assert planned is not None
    assert planned.fold == 0
    assert planned.utcoffset().total_seconds() == 7200


def test_allowed_month_and_weekday():
    now = datetime(2026, 11, 15, 7, 0, tzinfo=BERLIN)
    planned = schedule.next_scheduled(now, "08:00",
                                      [0, 1, 2, 3, 4, 5], [4, 5, 6, 7, 8, 9, 10])
    assert planned.month == 4 and planned.year == 2027
    assert planned.weekday() != 6


def test_no_match():
    now = datetime(2026, 11, 15, tzinfo=BERLIN)
    assert schedule.next_scheduled(now, "08:00", [], []) is None
