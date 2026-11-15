"""Live WetSoil binary status sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .entity import WetSoilEntity


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([
        WetSoilBinary(circuit, "running", "Watering"),
        WetSoilBinary(circuit, "allowed", "Automatic watering allowed"),
        WetSoilBinary(circuit, "raining", "Currently raining"),
    ])


class WetSoilBinary(WetSoilEntity, BinarySensorEntity):
    def __init__(self, circuit, key, name):
        super().__init__(circuit, key, name)

    @property
    def is_on(self):
        if self._key == "running":
            return self.circuit.running
        if self._key == "allowed":
            result = self.circuit.planned()
            return result > 0 if result is not None else None
        return self.circuit.weather.raining
