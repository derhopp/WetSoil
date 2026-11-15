"""Status entity for each WetSoil instance."""
from homeassistant.components.sensor import SensorEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([WetSoilStatus(entry)])

class WetSoilStatus(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_native_value = "Not implemented"

    def __init__(self, entry):
        self._attr_unique_id = f"{entry.unique_id}_status"
        self._attr_device_info = {
            "identifiers": {("wetsoil", entry.entry_id)},
            "name": entry.title,
            "manufacturer": "WetSoil",
        }
