# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path
from types import SimpleNamespace

import pytest

from gems_views_builder.input.component import (
    Component,
    build_component_port_connections,
    find_components_taxonomy_categories,
    group_components_by_taxonomy_category,
    save_component_port_connections,
)
from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system


def make_raw_component(component_id: str, model: str, properties: dict[str, str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model), properties=properties or {})


def test_locating_function_multiple_peers_raises(test_dataset_dir: Path) -> None:
    """A single location port must resolve to a unique peer: multiple peers is an error."""
    system = load_system(test_dataset_dir, resolve_libraries(test_dataset_dir / "library.yml"))
    if not system.connections:
        return

    components = [Component(component) for component in system.components]
    component_port_connections = build_component_port_connections(system.connections)
    save_component_port_connections(components, component_port_connections)

    ambiguous = [
        component for component in components if any(len(peers) > 1 for peers in component.connections.values())
    ]
    if not ambiguous:
        return

    component = ambiguous[0]
    port = next(port for port, peers in component.connections.items() if len(peers) > 1)
    with pytest.raises(ValueError):
        component.get_location(port)


def test_locating_function_zero_peers_raises(test_dataset_dir: Path) -> None:
    """A single location port with no connected peer is an error (must be unique)."""
    system = load_system(test_dataset_dir, resolve_libraries(test_dataset_dir / "library.yml"))
    assert len(system.components) > 0
    component = Component(system.components[0])
    # A port that is wired to nothing has zero peers, which is not a unique location.
    with pytest.raises(ValueError):
        component.get_location("this_port_is_not_connected_to_anything")


def test_get_location_zero_peers_raises_in_memory() -> None:
    """get_location raises when a port has no wired peer (built without dataset files)."""
    area = Component(make_raw_component("area", "basic_lib.area"))
    gen = Component(make_raw_component("gen", "basic_lib.gen"))
    connections = [
        SimpleNamespace(component1="gen", port1="balance_port", component2="area", port2="balance_port"),
    ]
    component_port_connections = build_component_port_connections(connections)
    save_component_port_connections([area, gen], component_port_connections)

    with pytest.raises(
        ValueError,
        match=r"Expected exactly one peer component for component 'area' on port 'spillage_port', but found 0",
    ):
        area.get_location("spillage_port")


def test_get_location_none_returns_own_id() -> None:
    component = Component(make_raw_component("area", "basic_lib.area"))
    assert component.get_location(None) == "area"


def test_find_components_taxonomy_categories() -> None:
    components = [Component(make_raw_component("gen", "lib.generator"))]
    find_components_taxonomy_categories(components, {"generator": "production"})
    assert components[0].taxonomy_category == "production"


def test_group_components_by_taxonomy_category() -> None:
    components = [
        Component(make_raw_component("gen_1", "lib.generator")),
        Component(make_raw_component("bus_1", "lib.bus")),
    ]
    components[0].taxonomy_category = "production"
    components[1].taxonomy_category = "balance"
    grouped = group_components_by_taxonomy_category(components)
    assert {c.id for c in grouped["production"]} == {"gen_1"}
    assert {c.id for c in grouped["balance"]} == {"bus_1"}


def test_match() -> None:
    from gems_views_builder.input.catalog import PropertySchema

    component = Component(make_raw_component("gen_1", "lib.generator", {"technology": "gas"}))
    assert component.match(None) is True
    assert component.match(PropertySchema(key="technology", value="gas")) is True
    assert component.match(PropertySchema(key="technology", value="nuclear")) is False
