"""WetSoil integration entrypoint: conservative prototype."""
from __future__ import annotations

from pathlib import Path
import logging
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, defaults, validate_config

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ("sensor", "switch", "button", "binary_sensor")


async def async_setup(hass, config):
    """Register frontend resources and authenticated configuration API."""
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths([
        StaticPathConfig("/wetsoil/wetsoil-card.js",
            str(Path(__file__).parent / "frontend" / "wetsoil-card.js"), True)
    ])
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_update)
    return True


async def async_setup_entry(hass, entry):
    """Initialize a new circuit in the disabled, safe state."""
    store = Store(hass, 1, f"wetsoil.{entry.entry_id}")
    saved = await store.async_load() or {}
    try:
        settings = validate_config(saved.get("config", defaults()))
    except ValueError:
        _LOGGER.exception("Invalid stored config for %s", entry.entry_id)
        settings = defaults()
    hass.data[DOMAIN][entry.entry_id] = {"entry": entry, "store": store, "config": settings}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Fail closed: initial prototype never operates hardware."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


@websocket_api.websocket_command({vol.Required("type"): "wetsoil/list"})
@callback
def ws_list(hass, connection, msg):
    """Read currently configured circuits."""
    connection.send_result(msg["id"], [
        {"entry_id": key, "name": val["entry"].title,
         "area_id": val["entry"].data.get("area_id"), "config": val["config"],
         "status": "not_implemented"}
        for key, val in hass.data[DOMAIN].items()
    ])


@websocket_api.websocket_command({
    vol.Required("type"): "wetsoil/update",
    vol.Required("entry_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_update(hass, connection, msg):
    """Persist validated changes; only HA administrators may modify them."""
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Admin required")
        return
    circuit = hass.data[DOMAIN].get(msg["entry_id"])
    if circuit is None:
        connection.send_error(msg["id"], "not_found", "Circuit not found")
        return
    try:
        settings = validate_config(msg["config"])
        for key, value in hass.data[DOMAIN].items():
            if key != msg["entry_id"] and set(value["config"]["valves"]) & set(settings["valves"]):
                raise ValueError("valve_already_assigned")
        if settings["start_mode"] == "chained":
            raise ValueError("chaining_not_implemented")
        if settings["automatic"]:
            raise ValueError("automatic_irrigation_not_implemented")
        await circuit["store"].async_save({"config": settings})
    except ValueError as exc:
        connection.send_error(msg["id"], "invalid_config", str(exc))
        return
    circuit["config"] = settings
    connection.send_result(msg["id"], {"config": settings})
