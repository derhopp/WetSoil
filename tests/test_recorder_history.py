"""Recorder backfill must never substitute incomplete measurements with zero."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

FILE = (Path(__file__).resolve().parents[1] /
        "custom_components/wetsoil/recorder_history.py")
SPEC = importlib.util.spec_from_file_location("wetsoil_recorder_unit", FILE)
RECORDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECORDER)
BERLIN = ZoneInfo("Europe/Berlin")


def mm(value, unit):
    if unit != "mm":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def observations(day, tz, kind="daily", quantity=1.0):
    """Produce a documented five-minute state history for a local day."""
    start = datetime.combine(day, datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(day+timedelta(days=1), datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
    amount = (end-start).total_seconds() / 300
    points = []
    for i in range(int(amount)):
        when = start + timedelta(minutes=5*i)
        value = i / 100 if kind == "daily" else quantity + i / 100
        points.append(SimpleNamespace(
            last_updated=when, state=str(value),
            attributes={"unit_of_measurement": "mm"}
        ))
    return points


@pytest.mark.parametrize("day,hours",[
    (datetime(2026,3,29).date(),23),
    (datetime(2026,10,25).date(),25),
])
def test_complete_day_across_dst(day,hours):
    points=observations(day,BERLIN)
    data=RECORDER.aggregate_days(points,day+timedelta(days=1),BERLIN,"daily",mm)
    assert data[day.isoformat()] == pytest.approx((hours*12-1)/100)


def test_three_completed_days_only_and_units():
    today=datetime(2026,11,16).date()
    points=[]
    for age in (3,2,1):
        points+=observations(today-timedelta(days=age),BERLIN)
    points+=observations(today,BERLIN)
    data=RECORDER.aggregate_days(points,today,BERLIN,"daily",mm)
    assert len(data)==3
    assert today.isoformat() not in data
    assert all(v==pytest.approx(2.87) for v in data.values())


def test_gap_and_sparse_states_do_not_fabricate_rainfall():
    today=datetime(2026,11,16).date()
    day=today-timedelta(days=1)
    rows=observations(day,BERLIN)
    rows=[point for i,point in enumerate(rows) if not 60<=i<=85]
    assert day.isoformat() not in RECORDER.aggregate_days(rows,today,BERLIN,"daily",mm)
    assert RECORDER.aggregate_days([rows[0],rows[-1]],today,BERLIN,"daily",mm)=={}


def test_unit_changes_and_counter_resets_are_invalid():
    today=datetime(2026,11,16).date()
    day=today-timedelta(days=1)
    rows=observations(day,BERLIN,kind="total")
    rows[120].attributes["unit_of_measurement"]="in"
    assert RECORDER.aggregate_days(rows,today,BERLIN,"total",mm)=={}
    rows=observations(day,BERLIN,kind="total")
    rows[120].state="0"
    assert RECORDER.aggregate_days(rows,today,BERLIN,"total",mm)=={}


def test_cumulative_total_uses_counter_delta():
    today=datetime(2026,11,16).date()
    day=today-timedelta(days=1)
    data=RECORDER.aggregate_days(
        observations(day,BERLIN,kind="total",quantity=500),
        today,BERLIN,"total",mm)
    assert data[day.isoformat()]==pytest.approx(2.87)


@pytest.mark.asyncio
async def test_missing_recorder_does_not_return_zero():
    hass=SimpleNamespace(config=SimpleNamespace(components=set()))
    days,quality=await RECORDER.read_recorder(
        hass,"sensor.rain",datetime(2026,11,16).date(),BERLIN,"total",mm)
    assert days=={}
    assert quality=="recorder_not_loaded"


def test_intensity_rate_units():
    assert RECORDER.intensity_mm_per_hour("1", "mm/h") == 1
    assert RECORDER.intensity_mm_per_hour("24", "mm/d") == 1
    assert RECORDER.intensity_mm_per_hour("1", "in/h") == pytest.approx(25.4)
    assert RECORDER.intensity_mm_per_hour("2", "in/d") == pytest.approx(2*25.4/24)
    for raw, unit in [("unknown","mm/h"),(-1,"mm/h"),(float("nan"),"mm/h"),
                      (3,"mm"),(3,"unknown")]:
        assert RECORDER.intensity_mm_per_hour(raw,unit) is None


def intensity_state(at, rate, unit="mm/h"):
    return SimpleNamespace(
        last_updated=at, state=str(rate),
        attributes={"unit_of_measurement":unit},
    )


def test_intensity_exact_72h_time_weighted():
    end=datetime(2026,11,16,12,tzinfo=timezone.utc)
    start=end-timedelta(hours=72)
    states=[intensity_state(start,0),
            intensity_state(start+timedelta(hours=12),2),
            intensity_state(start+timedelta(hours=36),0)]
    # 24 hours at 2 mm/h = 48mm total = 16mm per 24-hour equivalent.
    assert RECORDER.integrate_intensity(states,start,end)==pytest.approx(48)
    assert RECORDER.integrate_intensity([states[0]],start,end)==0


def test_intensity_rolling_72h_not_calendar_days_or_dst():
    # UTC elapsed-time window is always exactly 72 hours, even through DST.
    for end in (datetime(2026,3,30,12,tzinfo=timezone.utc),
                datetime(2026,10,26,12,tzinfo=timezone.utc)):
        start=end-timedelta(hours=72)
        assert RECORDER.integrate_intensity(
            [intensity_state(start,0.5)],start,end)==pytest.approx(36)


def test_intensity_unavailable_if_missing_start_or_unknown_interval():
    end=datetime(2026,11,16,12,tzinfo=timezone.utc)
    start=end-timedelta(hours=72)
    assert RECORDER.integrate_intensity(
        [intensity_state(start+timedelta(hours=1),2)],start,end) is None
    assert RECORDER.integrate_intensity(
        [intensity_state(start,1),intensity_state(start+timedelta(hours=2),"unavailable")],
        start,end) is None
    assert RECORDER.integrate_intensity(
        [intensity_state(start,1),intensity_state(start+timedelta(hours=2),1,"mm")],
        start,end) is None


def test_intensity_ignores_data_after_window():
    end=datetime(2026,11,16,12,tzinfo=timezone.utc)
    start=end-timedelta(hours=72)
    result=RECORDER.integrate_intensity(
        [intensity_state(start,1),intensity_state(end+timedelta(hours=1),100)],
        start,end)
    assert result==pytest.approx(72)
