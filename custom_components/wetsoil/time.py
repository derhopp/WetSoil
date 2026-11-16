"""Native start-time editor backed by the WetSoil circuit configuration."""
from datetime import time

from homeassistant.components.time import TimeEntity

from .entity import WetSoilEntity
from .validation import validate_all


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([WetSoilStartTime(circuit)])


class WetSoilStartTime(WetSoilEntity, TimeEntity):
    def __init__(self, circuit):
        super().__init__(circuit, "start_time", "Scheduled start time")

    @property
    def native_value(self):
        return time.fromisoformat(self.circuit.config["start_time"])

    async def async_set_value(self, value: time):
        async with self.hass.data["wetsoil_config_lock"]:
            settings = {**self.circuit.config, "start_time": value.strftime("%H:%M")}
            valid = validate_all(self.hass, self.circuit.entry.entry_id, settings)
            await self.circuit.update_config(valid)
