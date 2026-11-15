"""Manual start and stop buttons."""
from homeassistant.components.button import ButtonEntity
from .entity import WetSoilEntity


async def async_setup_entry(hass, entry, async_add_entities):
    circuit = hass.data["wetsoil"][entry.entry_id]
    async_add_entities([
        WetSoilButton(circuit, "manual_start", "Manual start"),
        WetSoilButton(circuit, "stop", "Immediate stop"),
    ])


class WetSoilButton(WetSoilEntity, ButtonEntity):
    def __init__(self, circuit, key, name):
        super().__init__(circuit, key, name)

    async def async_press(self):
        if self._key == "manual_start":
            await self.circuit.start(manual=True)
        else:
            await self.circuit.stop("manual_stop", abort=True)
