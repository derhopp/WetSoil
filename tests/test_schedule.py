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

def test_future_time_change_rearms_prior_attempt_same_day():
    old = {"start_mode":"time", "start_time":"07:00",
           "weekdays":[0,1,2,3,4,5,6], "months":[11]}
    new = {**old, "start_time":"15:00"}
    now = datetime(2026, 11, 16, 14, 14, tzinfo=BERLIN)
    assert schedule.should_rearm_today(old, new, "2026-11-16", now)
    assert schedule.next_scheduled(now, "15:00", new["weekdays"], new["months"]).date() == date(2026, 11, 16)


def test_past_time_or_unrelated_setting_does_not_rearm():
    old = {"start_mode":"time", "start_time":"07:00",
           "weekdays":[0,1,2,3,4,5,6], "months":[11]}
    now = datetime(2026, 11, 16, 14, 14, tzinfo=BERLIN)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"14:00"}, "2026-11-16", now)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"07:00"}, "2026-11-16", now)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"15:00"}, "2026-11-15", now)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"15:00", "months":[4]}, "2026-11-16", now)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"15:00", "weekdays":[1]}, "2026-11-16", now)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"15:00", "start_mode":"chained"}, "2026-11-16", now)


def test_exact_time_is_not_rearmed_and_dst_gap_is_excluded():
    old = {"start_mode":"time", "start_time":"01:00",
           "weekdays":list(range(7)), "months":list(range(1,13))}
    now = datetime(2026, 3, 29, 1, 30, tzinfo=BERLIN)
    assert not schedule.should_rearm_today(old, {**old, "start_time":"02:30"}, "2026-03-29", now)
    assert not schedule.should_rearm_today(
        {**old, "start_time":"07:00"}, {**old,"start_time":"15:00"},
        "2026-11-16", datetime(2026,11,16,15,0,tzinfo=BERLIN)
    )


def test_next_start_today_when_monday_and_november_allowed():
    now = datetime(2026, 11, 16, 14, 30, tzinfo=BERLIN)
    settings = {"start_mode":"time", "start_time":"16:00",
                "weekdays":[0,1,2,3,4,5], "months":[11]}
    assert schedule.today_schedule_reason(now, settings) == "today_allowed"
    assert schedule.next_scheduled(now,"16:00",settings["weekdays"],settings["months"]) == datetime(
        2026, 11, 16, 16, 0, tzinfo=BERLIN
    )


def test_schedule_diagnostic_explains_tomorrow_when_monday_excluded():
    now = datetime(2026, 11, 16, 14, 30, tzinfo=BERLIN)
    config = {"start_mode":"time", "start_time":"16:00",
              "weekdays":[1,2,3,4,5,6], "months":[11]}
    assert schedule.today_schedule_reason(now, config) == "weekday_excluded"
    assert schedule.next_scheduled(
        now,"16:00",config["weekdays"],config["months"]
    ).date() == date(2026,11,17)


def test_next_scheduled_does_not_repeat_consumed_day():
    now = datetime(2026,11,16,14,30,tzinfo=BERLIN)
    assert schedule.next_scheduled(
        now,"16:00",[0,1,2,3,4,5,6],[11],last_attempt="2026-11-16"
    ).date() == date(2026,11,17)


def test_configured_home_assistant_timezone_overrides_process_timezone(monkeypatch):
    from types import SimpleNamespace
    import sys
    from datetime import timezone
    class FakeDt:
        @staticmethod
        def utcnow():
            return datetime(2026,11,16,13,30,tzinfo=timezone.utc)
        @staticmethod
        def now():
            return datetime(2026,11,16,13,30,tzinfo=timezone.utc)
        @staticmethod
        def as_local(now):
            return now
    from types import ModuleType
    homeassistant=ModuleType("homeassistant")
    util=ModuleType("homeassistant.util")
    util.dt=FakeDt
    homeassistant.util=util
    monkeypatch.setitem(sys.modules,"homeassistant",homeassistant)
    monkeypatch.setitem(sys.modules,"homeassistant.util",util)
    assert schedule.configured_local_now(
        SimpleNamespace(config=SimpleNamespace(time_zone="Europe/Berlin"))
    ) == datetime(2026,11,16,14,30,tzinfo=BERLIN)
