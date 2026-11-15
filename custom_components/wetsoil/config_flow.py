"""Only name and area are required during initial WetSoil setup."""
from __future__ import annotations

from uuid import uuid4
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


class WetSoilConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create a distinct config entry for each irrigation circuit."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ask only for the circuit name and an existing area."""
        if user_input is not None:
            await self.async_set_unique_id(uuid4().hex)
            return self.async_create_entry(
                title=user_input["name"].strip(),
                data={"name": user_input["name"].strip(), "area_id": user_input["area_id"]},
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): selector.TextSelector(),
                vol.Required("area_id"): selector.AreaSelector(),
            }),
        )
