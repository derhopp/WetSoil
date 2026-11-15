"""Configuration consistency, valve conflict and chain graph tests."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


@pytest.fixture()
def modules(monkeypatch):
    base=Path(__file__).resolve().parents[1] / "custom_components/wetsoil"
    package=ModuleType("wetsoil_test_pkg")
    package.__path__=[str(base)]
    monkeypatch.setitem(sys.modules,"wetsoil_test_pkg",package)
    for name in ("const","validation"):
        spec=importlib.util.spec_from_file_location(
            "wetsoil_test_pkg."+name,base/(name+".py"))
        obj=importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules,spec.name,obj)
        spec.loader.exec_module(obj)
    return (
        sys.modules["wetsoil_test_pkg.const"],
        sys.modules["wetsoil_test_pkg.validation"],
    )


class FakeHass:
    def __init__(self, values):
        self.data={"wetsoil":values}
        self.states=self

    def get(self, entity):
        return object() if entity in ("switch.a","switch.b","weather.a") else None


def test_two_circuits_cannot_share_valve(modules):
    const, validation=modules
    cfg=const.defaults()
    cfg["valves"]=["switch.a"]
    hass=FakeHass({"one":{"config":cfg},"two":{"config":const.defaults()}})
    newer=const.defaults()
    newer["valves"]=["switch.a"]
    with pytest.raises(ValueError,match="shared_valve"):
        validation.validate_all(hass,"two",newer)


def test_cycles_and_multiple_successors(modules):
    const, validation=modules
    a,b,c=(const.defaults() for _ in range(3))
    b.update(start_mode="chained",predecessor="one")
    c.update(start_mode="chained",predecessor="one")
    hass=FakeHass({"one":{"config":a},"two":{"config":b},"three":{"config":c}})
    with pytest.raises(ValueError,match="invalid_predecessor"):
        validation.validate_all(hass,"three",c)
    c["predecessor"]="two"
    a.update(start_mode="chained",predecessor="three")
    with pytest.raises(ValueError,match="cyclic_predecessor"):
        validation.validate_all(hass,"one",a)


def test_valid_linear_chain(modules):
    const, validation=modules
    a,b,c=(const.defaults() for _ in range(3))
    b.update(start_mode="chained",predecessor="one")
    c.update(start_mode="chained",predecessor="two")
    hass=FakeHass({"one":{"config":a},"two":{"config":b},"three":{"config":c}})
    assert validation.validate_all(hass,"three",c)["predecessor"]=="two"
