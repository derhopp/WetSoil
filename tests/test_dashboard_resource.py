"""Isolated tests for non-destructive Lovelace resource registration."""
import ast
import asyncio
import hashlib
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def register(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    source = root / "custom_components/wetsoil/__init__.py"
    tree = ast.parse(source.read_text())
    method = next(
        node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_register_dashboard_resource"
    )
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    const = ModuleType("homeassistant.components.lovelace.const")
    const.LOVELACE_DATA = "lovelace"
    const.MODE_STORAGE = "storage"
    monkeypatch.setitem(sys.modules, const.__name__, const)
    for path in ("homeassistant", "homeassistant.components",
                 "homeassistant.components.lovelace"):
        monkeypatch.setitem(sys.modules, path, ModuleType(path))
    environment = {
        "__file__": str(source),
        "Path": Path,
        "hashlib": hashlib,
        "_LOGGER": logging.getLogger("wetsoil-test"),
    }
    exec(compile(module, str(source), "exec"), environment)
    return environment["_register_dashboard_resource"]


class Resources:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.loaded = False
        self.creates = 0
        self.updates = 0

    async def async_get_info(self):
        self.loaded = True
        return {"resources": len(self.items)}

    def async_items(self):
        assert self.loaded, "must load stored resources before mutation"
        return self.items

    async def async_create_item(self, data):
        self.creates += 1
        self.items.append({"id": f"generated-{self.creates}",
                           "type": data["res_type"], "url": data["url"]})

    async def async_update_item(self, id, updates):
        self.updates += 1
        item = next(x for x in self.items if x["id"] == id)
        item.update({"url": updates["url"], "type": updates["res_type"]})


@pytest.mark.asyncio
async def test_register_does_not_destroy_existing_resources_or_duplicate(register):
    resources = Resources([{"id": "other", "url": "/local/other.js", "type": "module"}])
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(
        resource_mode="storage", resources=resources)})
    await register(hass)
    await register(hass)
    assert resources.creates == 1
    assert resources.updates == 0
    assert len(resources.items) == 2
    assert resources.items[0]["url"] == "/local/other.js"
    assert resources.items[1]["url"].startswith("/wetsoil/wetsoil-card.js?v=")


@pytest.mark.asyncio
async def test_old_resource_version_gets_updated_in_place(register):
    resources = Resources([{"id": "wetsoil", "url": "/wetsoil/wetsoil-card.js",
                            "type": "module"}])
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(
        resource_mode="storage", resources=resources)})
    await register(hass)
    assert resources.creates == 0
    assert resources.updates == 1
    assert resources.items[0]["id"] == "wetsoil"
    assert "?v=" in resources.items[0]["url"]


@pytest.mark.asyncio
async def test_yaml_resources_are_left_alone(register):
    resources = Resources()
    hass = SimpleNamespace(data={"lovelace": SimpleNamespace(
        resource_mode="yaml", resources=resources)})
    await register(hass)
    assert not resources.loaded
    assert resources.creates == resources.updates == 0
