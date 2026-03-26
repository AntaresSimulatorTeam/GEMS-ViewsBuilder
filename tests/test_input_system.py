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

import pytest
from gems.study.parsing import InputSystem, parse_yaml_components  # type: ignore


def test_input_system_using(test_dataset_dir: Path) -> None:
    input_system_path = test_dataset_dir / "system.yml"
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path) as file:
        input_system = parse_yaml_components(file)
    assert input_system is not None
    assert isinstance(input_system, InputSystem)


def test_locating_function(test_dataset_dir: Path) -> None:
    """LOCATING_FUNCTION: None -> component_id, string -> peer id, tuple -> tuple of peer ids."""
    from gems_views_builder import InputSystem as GemsViewsInputSystem

    system_path = test_dataset_dir / "system.yml"
    assert system_path.exists(), f"System file not found: {system_path}"
    system = GemsViewsInputSystem.from_file(system_path)

    # location_port is None -> return component_id (generic)
    assert len(system.components) > 0
    any_component_id = system.components[0].id
    assert system.get_location(any_component_id, None) == any_component_id

    # location_port is string -> return peer component id (pick a real connection from the dataset)
    if not system.connections:
        pytest.skip("No connections in this dataset's system.yml")

    conn0 = system.connections[0]
    c1 = getattr(conn0, "component1", None)
    p1 = getattr(conn0, "port1", None)
    c2 = getattr(conn0, "component2", None)
    p2 = getattr(conn0, "port2", None)
    if not (
        isinstance(c1, str)
        and c1
        and isinstance(p1, str)
        and p1
        and isinstance(c2, str)
        and c2
        and isinstance(p2, str)
        and p2
    ):
        pytest.skip("Connection entries missing component/port fields")

    assert system.get_location(c1, p1) == c2
    assert system.get_location(c2, p2) == c1

    # location_port is tuple -> return tuple of peer ids (requires at least two ports connected for the same component)
    ports_by_component: dict[str, list[str]] = {}
    for conn in system.connections:
        c1x = getattr(conn, "component1", None)
        p1x = getattr(conn, "port1", None)
        c2x = getattr(conn, "component2", None)
        p2x = getattr(conn, "port2", None)
        if isinstance(c1x, str) and isinstance(p1x, str) and c1x and p1x:
            ports_by_component.setdefault(c1x, []).append(p1x)
        if isinstance(c2x, str) and isinstance(p2x, str) and c2x and p2x:
            ports_by_component.setdefault(c2x, []).append(p2x)

    comp_with_two = next((cid for cid, ports in ports_by_component.items() if len(set(ports)) >= 2), None)
    if comp_with_two is None:
        pytest.skip("No component with >=2 connected ports in this dataset")

    unique_ports = list(dict.fromkeys(ports_by_component[comp_with_two]))
    port_a, port_b = unique_ports[0], unique_ports[1]
    peer_a = system.get_location(comp_with_two, port_a)
    peer_b = system.get_location(comp_with_two, port_b)
    assert system.get_location(comp_with_two, (port_a, port_b)) == (peer_a, peer_b)
