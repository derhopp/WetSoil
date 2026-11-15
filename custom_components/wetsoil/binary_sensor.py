"""Safe default runtime sensor."""
from homeassistant.components.binary_sensor import BinarySensorEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([WetSoilRunning(entry)])

class WetSoilRunning(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Watering"
    _attr_is_on = False

    def __init__(self, entry):
        self._attr_unique_id = f"{entry.unique_id}_running"
        self._attr_device_info = {"identifiers": {("wetsoil", entry.entry_id)}, "name": entry.title}
