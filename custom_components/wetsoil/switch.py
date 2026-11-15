"""Disabled automation switch until safe backend implementation is ready."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([WetSoilSwitch(entry)])

class WetSoilSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Automatic irrigation"
    _attr_is_on = False

    def __init__(self, entry):
        self._attr_unique_id = f"{entry.unique_id}_automatic"
        self._attr_device_info = {"identifiers": {("wetsoil", entry.entry_id)}, "name": entry.title}

    async def async_turn_on(self, **kwargs):
        raise HomeAssistantError("Automatic irrigation is not implemented")

    async def async_turn_off(self, **kwargs):
        return
