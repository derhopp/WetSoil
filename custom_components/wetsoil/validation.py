"""Validate cross-circuit references and entity types before saving."""
from __future__ import annotations

from .const import DOMAIN, validate_config


def validate_all(hass, updated_id, updated):
    """No shared valves, missing references or non-linear cycles."""
    settings = validate_config(updated)
    circuits = {
        entry_id: value["config"] for entry_id, value
        in hass.data[DOMAIN].items()
    }
    circuits[updated_id] = settings
    used = set()
    parents = set()
    for entry_id, value in circuits.items():
        for key, domain in (("weather_entity", "weather"),
                            ("rain_sensor", "binary_sensor"),
                            ("precipitation_sensor", "sensor")):
            entity = value[key]
            if entity and (not entity.startswith(domain + ".")
                           or hass.states.get(entity) is None):
                raise ValueError("invalid_entity:" + key)
        for valve in value["valves"]:
            if valve in used:
                raise ValueError("shared_valve:" + valve)
            if hass.states.get(valve) is None:
                raise ValueError("missing_valve:" + valve)
            used.add(valve)
        parent = value["predecessor"] if value["start_mode"] == "chained" else None
        if parent:
            if parent == entry_id or parent not in circuits or parent in parents:
                raise ValueError("invalid_predecessor")
            parents.add(parent)
    for entry_id in circuits:
        seen = set()
        key = entry_id
        while key:
            if key in seen:
                raise ValueError("cyclic_predecessor")
            seen.add(key)
            value = circuits[key]
            key = value["predecessor"] if value["start_mode"] == "chained" else None
    return settings
