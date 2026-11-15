"""Pure port of the existing WetSoil Node-RED irrigation algorithm."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Calculation:
    """Computed time and transparent factors; None means unavailable."""
    seconds: float | None
    temp_factor: float | None
    rain_today_factor: float | None
    rain_3d_factor: float | None
    reason: str


def calculate(
    base_seconds: float,
    max_rain_today: float,
    max_rain_3d: float,
    min_temp: float,
    max_temp: float,
    rain_today: float | None,
    rain_3d: float | None,
    temperature: float | None,
    raining: bool | None,
) -> Calculation:
    """Apply strict Node-RED thresholds and JavaScript Math.round semantics."""
    values = (rain_today, rain_3d, temperature)
    if any(v is None or isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) for v in values) or type(raining) is not bool:
        return Calculation(None, None, None, None, "weather_unavailable")
    if any(v < 0 for v in (rain_today, rain_3d)):
        return Calculation(None, None, None, None, "invalid_precipitation")
    if max_rain_today <= 0 or max_rain_3d <= 0 or max_temp <= min_temp or base_seconds <= 0:
        return Calculation(None, None, None, None, "invalid_parameters")
    temp_factor = (
        1 + (temperature - min_temp) / (2 * (max_temp - min_temp))
        if temperature < max_temp else 1.5
    )
    today_factor = 1 - rain_today / max_rain_today
    historic_factor = 1 - rain_3d / max_rain_3d
    if raining:
        reason = "raining"
    elif rain_3d >= max_rain_3d:
        reason = "rain_3d_limit"
    elif rain_today >= max_rain_today:
        reason = "rain_today_limit"
    elif temperature <= min_temp:
        reason = "temperature_limit"
    else:
        reason = "allowed"
    if reason != "allowed":
        return Calculation(0.0, temp_factor, today_factor, historic_factor, reason)
    raw = base_seconds * historic_factor * today_factor * temp_factor
    # For non-negative values: JavaScript Math.round(x) == floor(x + .5).
    rounded = math.floor(raw + 0.5)
    seconds = max(float(rounded), base_seconds / 2)
    return Calculation(seconds, temp_factor, today_factor, historic_factor, reason)
