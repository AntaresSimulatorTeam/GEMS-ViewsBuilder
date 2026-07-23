# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

from gems_views_builder.input.component import (
    Component,
    group_components_by_taxon,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.component.location import Location


def make_raw_component(component_id: str, model: str, properties: dict[str, str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model), properties=properties or {})


def test_get_location_none_returns_own_id() -> None:
    component = Component(make_raw_component("area", "basic_lib.area"))
    component.locations[(None, "balance")] = Location(id=component.id, properties=component.properties)
    assert component.is_located_at(None, "balance") is True
    assert component.resolve_location(None, "balance", []) == ["area"]


def test_supply_components_with_taxonomy_categories() -> None:
    components = [Component(make_raw_component("gen", "lib.generator"))]
    supply_components_with_taxonomy_categories(components, {"generator": "production"})
    assert components[0].taxonomy_category == "production"


def test_group_components_by_taxonomy_category() -> None:
    components = [
        Component(make_raw_component("gen_1", "lib.generator")),
        Component(make_raw_component("bus_1", "lib.bus")),
    ]
    components[0].taxonomy_category = "production"
    components[1].taxonomy_category = "balance"
    grouped = group_components_by_taxon(components)
    assert {c.id for c in grouped["production"]} == {"gen_1"}
    assert {c.id for c in grouped["balance"]} == {"bus_1"}


def test_match() -> None:
    from gems_views_builder.input.catalog import PropertySchema

    component = Component(make_raw_component("gen_1", "lib.generator", {"technology": "gas"}))
    assert component.match(None) is True
    assert component.match(PropertySchema(key="technology", value="gas")) is True
    assert component.match(PropertySchema(key="technology", value="nuclear")) is False
