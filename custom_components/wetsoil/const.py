"""Configuration defaults for WetSoil."""
from __future__ import annotations

from copy import deepcopy
import math
import re

DOMAIN = "wetsoil"
PLATFORMS = ("switch", "button", "binary_sensor", "sensor")
CARD_URL = "/wetsoil/wetsoil-card.js"
DEFAULTS = {
    "automatic": False,
    "weather_entity": None,
    "rain_sensor": None,
    "precipitation_sensor": None,
    "precipitation_sensor_kind": "total",
    "valves": [],
    "base_seconds": 30.0,
    "max_rain_today": 2.0,
    "max_rain_3d": 2.0,
    "min_temp": 23.0,
    "max_temp": 35.0,
    "max_runtime": 3600.0,
    "weekdays": [0, 1, 2, 3, 4, 5],
    "months": [4, 5, 6, 7, 8, 9, 10],
    "start_time": "08:00",
    "start_mode": "time",
    "predecessor": None,
}
NUMERIC = ("base_seconds", "max_rain_today", "max_rain_3d",
           "min_temp", "max_temp", "max_runtime")
ENTITY_KEYS = ("weather_entity", "rain_sensor", "precipitation_sensor")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def defaults() -> dict:
    """Return independent mutable defaults."""
    return deepcopy(DEFAULTS)


def validate_config(data: dict) -> dict:
    """Validate a complete configuration; fail without mutating input."""
    if set(data) != set(DEFAULTS):
        raise ValueError("unexpected_configuration_keys")
    c = deepcopy(data)
    if type(c["automatic"]) is not bool:
        raise ValueError("invalid_automatic")
    for k in NUMERIC:
        if isinstance(c[k], bool) or not isinstance(c[k], (int, float)):
            raise ValueError(f"invalid_{k}")
        c[k] = float(c[k])
        if not math.isfinite(c[k]):
            raise ValueError(f"invalid_{k}")
    for k in ("base_seconds", "max_rain_today", "max_rain_3d", "max_runtime"):
        if c[k] <= 0:
            raise ValueError(f"invalid_{k}")
    if c["max_temp"] <= c["min_temp"]:
        raise ValueError("invalid_temperature_range")
    if c["max_runtime"] > 86400:
        raise ValueError("invalid_max_runtime")
    if not isinstance(c["start_time"], str) or not TIME_RE.fullmatch(c["start_time"]):
        raise ValueError("invalid_start_time")
    if c["start_mode"] not in ("time", "chained"):
        raise ValueError("invalid_start_mode")
    if c["precipitation_sensor_kind"] not in ("total", "daily"):
        raise ValueError("invalid_sensor_kind")
    for key in ENTITY_KEYS + ("predecessor",):
        if c[key] is not None and (not isinstance(c[key], str) or not c[key]):
            raise ValueError(f"invalid_{key}")
    if c["start_mode"] == "chained" and not c["predecessor"]:
        raise ValueError("missing_predecessor")
    if c["start_mode"] == "time" and c["predecessor"]:
        raise ValueError("unexpected_predecessor")
    if not isinstance(c["valves"], list) or any(
        not isinstance(s, str) or not s.startswith("switch.") for s in c["valves"]
    ) or len(c["valves"]) != len(set(c["valves"])):
        raise ValueError("invalid_valves")
    for key, lower, upper in (("weekdays", 0, 6), ("months", 1, 12)):
        v = c[key]
        if not isinstance(v, list) or any(
            type(n) is not int or not lower <= n <= upper for n in v
        ) or len(v) != len(set(v)):
            raise ValueError(f"invalid_{key}")
    return c
