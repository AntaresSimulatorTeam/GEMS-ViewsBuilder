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
from gems.study.parsing import SystemSchema, parse_yaml_components  # type: ignore

from gems_views_builder import load_system


def test_input_system_using(test_dataset_dir: Path) -> None:
    input_system_path = test_dataset_dir / "system.yml"
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path, encoding="utf-8") as f:
        input_system = parse_yaml_components(f)
    assert input_system is not None
    assert isinstance(input_system, SystemSchema)


def test_locating_function_multiple_peers_raises(test_dataset_dir: Path) -> None:
    """A single location port must resolve to a unique peer: multiple peers is an error."""
    system = load_system(test_dataset_dir)

    if not system.connections:
        return

    ambiguous = [(cid, pid) for (cid, pid), peers in system._component_port_connections.items() if len(peers) > 1]
    if not ambiguous:
        return

    cid, pid = ambiguous[0]
    with pytest.raises(ValueError):
        system.get_location(cid, pid)


def test_locating_function(test_dataset_dir: Path) -> None:
    """LOCATING_FUNCTION: None -> component_id, string -> unique peer id (or error)."""
    assert (test_dataset_dir / "system.yml").exists()
    system = load_system(test_dataset_dir)

    # location_port is None -> return component_id (generic)
    assert len(system.components) > 0
    any_component_id = system.components[0].id
    assert system.get_location(any_component_id, None) == any_component_id

    # location_port is a string → it must resolve to exactly one peer (returned as a
    # str). A port wired to multiple peers is ambiguous and raises for metric building.
    if not system._component_port_connections:
        pytest.skip("No connections in this dataset's system.yml")

    for (component, port), peers in system._component_port_connections.items():
        if len(peers) == 1:
            assert system.get_location(component, port) == next(iter(peers))
        else:
            with pytest.raises(ValueError):
                system.get_location(component, port)
