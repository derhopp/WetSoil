"""Non-operational buttons: fail closed rather than simulate valve action."""
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([WetSoilButton(entry, "start", "Manual start"),
                        WetSoilButton(entry, "stop", "Stop")])

class WetSoilButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, key, name):
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_name = name
        self._attr_device_info = {"identifiers": {("wetsoil", entry.entry_id)}, "name": entry.title}

    async def async_press(self):
        raise HomeAssistantError("Valve control is not implemented")
