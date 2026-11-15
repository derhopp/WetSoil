"""Status, calculations, weather data, and configuration diagnostics."""
from homeassistant.components.sensor import SensorEntity
from .entity import WetSoilEntity

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
        if unit is not None:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        snapshot = self.circuit.snapshot()
        special = {
            "temp_factor": snapshot["factors"]["temp"],
            "today_factor": snapshot["factors"]["today"],
            "history_factor": snapshot["factors"]["history"],
            "last_start": snapshot["started_at"],
            "last_end": snapshot["last_end"],
            "config": "configured",
            "events": (snapshot["events"][-1] if snapshot["events"] else None),
        }
        return special[self._key] if self._key in special else snapshot.get(self._key)

    @property
    def extra_state_attributes(self):
        if self._key == "config":
            return {"settings": self.circuit.config}
        if self._key == "events":
            return {"history": list(self.circuit.events)}
        return None
