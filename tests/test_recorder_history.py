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
