"""Editable native numeric parameters share the central backend configuration."""
from homeassistant.components.number import NumberEntity
from .entity import WetSoilEntity
from .validation import validate_all

NUMBERS = {
    "base_seconds": ("Base watering duration", 0.5, 86400, "s"),
    "max_rain_today": ("Daily precipitation limit", 0.01, 1000, "mm"),
    "max_rain_3d": ("3-day precipitation limit", 0.01, 1000, "mm"),
    "min_temp": ("Lower temperature threshold", -50, 70, "°C"),
    "max_temp": ("Upper temperature threshold", -49, 90, "°C"),
    "max_runtime": ("Maximum safety runtime", 1, 86400, "s"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([
        WetSoilNumber(circuit, key, *definition)
        for key, definition in NUMBERS.items()
    ])


class WetSoilNumber(WetSoilEntity, NumberEntity):
    def __init__(self, circuit, key, name, minimum, maximum, unit):
        super().__init__(circuit, key, name)
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = 0.5 if unit == "s" else (0.1 if unit == "°C" else 0.01)
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.circuit.config[self._key]

    async def async_set_native_value(self, value):
        async with self.hass.data["wetsoil_config_lock"]:
            settings = {**self.circuit.config, self._key: value}
            valid = validate_all(self.hass, self.circuit.entry.entry_id, settings)
            await self.circuit.update_config(valid)
