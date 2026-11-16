"""Native selector for measured precipitation sensor type."""
from homeassistant.components.select import SelectEntity

from .entity import WetSoilEntity
from .validation import validate_all

OPTIONS = ["total", "daily", "intensity"]


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([WetSoilPrecipitationKind(circuit)])


class WetSoilPrecipitationKind(WetSoilEntity, SelectEntity):
    _attr_options = OPTIONS

    def __init__(self, circuit):
        super().__init__(circuit, "precipitation_sensor_kind", "Precipitation sensor type")

    @property
    def current_option(self):
        return self.circuit.config["precipitation_sensor_kind"]

    async def async_select_option(self, option: str):
        if option not in OPTIONS:
            raise ValueError("invalid_sensor_kind")
        async with self.hass.data["wetsoil_config_lock"]:
            settings = {**self.circuit.config, "precipitation_sensor_kind": option}
            valid = validate_all(self.hass, self.circuit.entry.entry_id, settings)
            await self.circuit.update_config(valid)
