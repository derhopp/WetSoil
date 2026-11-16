"""Shared entity identity and live update subscription."""
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from .controller import EVENT
from .text_labels import language_for, name_text


class WetSoilEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, circuit, key, name):
        self.circuit = circuit
        self._key = key
        self._attr_name = name_text(name, language_for(circuit.hass))
        self._attr_unique_id = f"{circuit.entry.unique_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, circuit.entry.entry_id)},
            "name": circuit.entry.title,
            "manufacturer": "WetSoil",
        }

    async def async_added_to_hass(self):
        self.async_on_remove(self.hass.bus.async_listen(EVENT, self._on_event))

    @callback
    def _on_event(self, event):
        if event.data.get("entry_id") == self.circuit.entry.entry_id:
            self.async_write_ha_state()
