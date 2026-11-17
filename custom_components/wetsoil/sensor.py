"""Status, calculations, weather data, and configuration diagnostics."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt as dt_util
from .schedule import next_scheduled
from .entity import WetSoilEntity
from .text_labels import event_text, language_for, status_text

DESCRIPTIONS = {
    "status": ("State", None),
    "reason": ("Blocking reason", None),
    "computed_seconds": ("Computed watering duration", "s"),
    "planned_seconds": ("Planned watering duration", "s"),
    "remaining_seconds": ("Remaining watering duration", "s"),
    "temperature": ("Daily forecast maximum temperature", "°C"),
    "rain_today": ("Forecast precipitation today", "mm"),
    "rain_3d": ("Mean precipitation last three days", "mm"),
    "quality": ("Weather data quality", None),
    "temp_factor": ("Temperature factor", None),
    "today_factor": ("Today precipitation factor", None),
    "history_factor": ("Historical precipitation factor", None),
    "last_start": ("Last start", None),
    "last_end": ("Last end", None),
    "next_start": ("Next scheduled start", None),
    "config": ("Configuration", None),
    "events": ("Last action", None),
}


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([
        WetSoilSensor(circuit, key, name, unit)
        for key, (name, unit) in DESCRIPTIONS.items()
    ])


class WetSoilSensor(WetSoilEntity, SensorEntity):
    def __init__(self, circuit, key, name, unit):
        super().__init__(circuit, key, name)
        self._next_start_cache = None
        if unit is not None:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        """Read only this sensor's fields; never build a full WebSocket snapshot."""
        circuit = self.circuit
        weather = circuit.weather
        key = self._key
        if key == "status":
            return status_text(circuit.status, language_for(circuit.hass))
        if key == "reason":
            raw = (circuit.error or
                   ("rain_sources_disagree" if weather.rain_source_disagreement
                    else circuit.calculation().reason))
            return status_text(raw, language_for(circuit.hass))
        if key == "computed_seconds":
            return circuit.calculation().seconds
        if key == "planned_seconds":
            return circuit.planned()
        if key == "remaining_seconds":
            if circuit.ends is None:
                return 0
            end = dt_util.parse_datetime(circuit.ends)
            return max(0, (end - dt_util.utcnow()).total_seconds()) if end else None
        if key in ("temperature", "rain_today", "rain_3d", "quality"):
            value = getattr(weather, key)
            if key == "quality":
                return status_text(value, language_for(circuit.hass))
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return round(value, 1 if key == "temperature" else 2)
            return value
        if key in ("temp_factor", "today_factor", "history_factor"):
            calc = circuit.calculation()
            return getattr(calc, {
                "temp_factor": "temp_factor",
                "today_factor": "rain_today_factor",
                "history_factor": "rain_3d_factor",
            }[key])
        if key == "last_start":
            return circuit.started
        if key == "last_end":
            return circuit.ended
        if key == "next_start":
            if circuit.config["start_mode"] == "chained":
                return "after:" + circuit.config["predecessor"]
            now = dt_util.now()
            config_key = (
                circuit.config["start_time"],
                tuple(circuit.config["weekdays"]),
                tuple(circuit.config["months"]),
            )
            cached = self._next_start_cache
            if cached and cached[0] == config_key and now < cached[1]:
                return cached[2]
            next_time = next_scheduled(
                now, circuit.config["start_time"],
                circuit.config["weekdays"], circuit.config["months"])
            value = next_time.isoformat() if next_time else None
            from datetime import timedelta
            self._next_start_cache = (config_key, now + timedelta(seconds=60), value)
            return value
        if key == "config":
            return "configured"
        if key == "events":
            return event_text(
                circuit.events[-1] if circuit.events else None,
                language_for(circuit.hass),
            )
        return None

    @property
    def extra_state_attributes(self):
        if self._key == "config":
            return {"settings": self.circuit.config}
        if self._key == "events":
            raw = list(self.circuit.events)
            language = language_for(self.circuit.hass)
            return {
                "history": raw,
                "translated_history": [event_text(item, language) for item in raw],
                "raw_code": raw[-1] if raw else None,
            }
        if self._key == "status":
            return {"raw_code": self.circuit.status}
        if self._key == "quality":
            return {"raw_code": self.circuit.weather.quality}
        if self._key == "reason":
            return {"raw_code": (
                self.circuit.error
                or ("rain_sources_disagree" if self.circuit.weather.rain_source_disagreement
                    else self.circuit.calculation().reason)
            )}
        return None
