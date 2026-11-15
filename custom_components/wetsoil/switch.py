"""WetSoil native automation switch."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import WetSoilEntity
from .validation import validate_all


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AutomaticSwitch(hass.data["wetsoil"][entry.entry_id])])


class AutomaticSwitch(WetSoilEntity, SwitchEntity):
    def __init__(self, circuit):
        super().__init__(circuit, "automatic", "Automatic watering")

    @property
    def is_on(self):
        return self.circuit.config["automatic"]

    async def async_turn_on(self, **kwargs):
        if self.circuit.weather.quality != "ready" or not self.circuit.config["valves"]:
            raise HomeAssistantError("Complete weather history and valves are required")
        config = validate_all(self.hass, self.circuit.entry.entry_id, {
            **self.circuit.config, "automatic": True
        })
        await self.circuit.update_config(config)

    async def async_turn_off(self, **kwargs):
        await self.circuit.update_config({**self.circuit.config, "automatic": False})
