"""WetSoil Home Assistant integration and authenticated frontend API."""
from __future__ import annotations

from pathlib import Path
import hashlib
import logging
import asyncio
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .controller import Circuit
from .validation import validate_all

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ("sensor", "binary_sensor", "switch", "button", "number")


async def async_setup(hass, config):
    """Register a single frontend URL and authenticated WebSocket commands."""
    hass.data.setdefault(DOMAIN, {})
    hass.data.setdefault(DOMAIN + "_config_lock", asyncio.Lock())
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/wetsoil/wetsoil-card.js",
            str(Path(__file__).parent / "frontend" / "wetsoil-card.js"),
            cache_headers=False,
        )
    ])
    for command in (ws_list, ws_update, ws_action):
        websocket_api.async_register_command(hass, command)
    return True


async def _register_dashboard_resource(hass):
    """Register the bundled card once in UI-managed Lovelace resources.

    Storage resources must be loaded BEFORE mutation. In YAML mode, never
    alter the user's file. A hash in the URL refreshes cached browser modules.
    """
    try:
        from homeassistant.components.lovelace.const import (
            LOVELACE_DATA, MODE_STORAGE,
        )
        lovelace = hass.data.get(LOVELACE_DATA)
        if lovelace is None or lovelace.resource_mode != MODE_STORAGE:
            _LOGGER.info(
                "WetSoil dashboard resource needs manual registration in YAML mode "
                "or until Lovelace is ready"
            )
            return
        resources = lovelace.resources
        # Guard against preloaded=false resource collections (historical
        # Lovelace storage corruption). async_get_info() ensures loading.
        await resources.async_get_info()
        base = "/wetsoil/wetsoil-card.js"
        source = Path(__file__).parent / "frontend" / "wetsoil-card.js"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        url = f"{base}?v={digest}"
        matched = [
            item for item in resources.async_items()
            if item.get("url", "").split("?")[0] == base
        ]
        if matched:
            current = matched[0]
            if current.get("url") != url or current.get("type") != "module":
                await resources.async_update_item(
                    current["id"], {"url": url, "res_type": "module"}
                )
        else:
            await resources.async_create_item({"url": url, "res_type": "module"})
    except Exception:
        _LOGGER.exception("WetSoil Lovelace resource registration failed")


async def async_setup_entry(hass, entry):
    """Load a circuit and expose native Home Assistant entities."""
    circuit = Circuit(hass, entry)
    await circuit.setup()
    hass.data[DOMAIN][entry.entry_id] = circuit
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _register_dashboard_resource(hass)
    area = entry.data.get("area_id")
    if area:
        registry = dr.async_get(hass)
        device = registry.async_get_device_by_identifier(
            (DOMAIN, entry.entry_id), entry.entry_id
        )
        if device and not device.area_id:
            registry.async_update_device(device.id, area_id=area)
    return True


async def async_unload_entry(hass, entry):
    """Unload without sending actuator commands."""
    circuit = hass.data[DOMAIN][entry.entry_id]
    await circuit.shutdown()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


@websocket_api.websocket_command({vol.Required("type"): "wetsoil/list"})
@callback
def ws_list(hass, connection, msg):
    """Read live snapshots, including centrally stored settings."""
    connection.send_result(msg["id"], [
        circuit.snapshot() for circuit in hass.data[DOMAIN].values()
    ])


@websocket_api.websocket_command({
    vol.Required("type"): "wetsoil/update",
    vol.Required("entry_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_update(hass, connection, msg):
    """Require administrator privileges and validate globally before saving."""
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Admin required")
        return
    circuit = hass.data[DOMAIN].get(msg["entry_id"])
    if circuit is None:
        connection.send_error(msg["id"], "not_found", "Circuit not found")
        return
    try:
        async with hass.data[DOMAIN + "_config_lock"]:
            settings = validate_all(hass, msg["entry_id"], msg["config"])
            await circuit.update_config(settings)
    except (ValueError, RuntimeError) as err:
        connection.send_error(msg["id"], "invalid_config", str(err))
        return
    connection.send_result(msg["id"], circuit.snapshot())


@websocket_api.websocket_command({
    vol.Required("type"): "wetsoil/action",
    vol.Required("entry_id"): str,
    vol.Required("action"): vol.In(("start", "stop", "enable", "disable", "reset_today")),
})
@websocket_api.async_response
async def ws_action(hass, connection, msg):
    """All hardware and configuration actions require admin privileges."""
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Admin required")
        return
    circuit = hass.data[DOMAIN].get(msg["entry_id"])
    if circuit is None:
        connection.send_error(msg["id"], "not_found", "Circuit not found")
        return
    try:
        command = msg["action"]
        if command == "start":
            await circuit.start(manual=True)
        elif command == "stop":
            await circuit.stop("manual_stop", abort=True)
        elif command == "reset_today":
            await circuit.reset_today_status()
        else:
            async with hass.data[DOMAIN + "_config_lock"]:
                settings = {**circuit.config, "automatic": command == "enable"}
                settings = validate_all(hass, msg["entry_id"], settings)
                await circuit.update_config(settings)
    except (ValueError, RuntimeError) as err:
        connection.send_error(msg["id"], "action_failed", str(err))
        return
    connection.send_result(msg["id"], circuit.snapshot())
