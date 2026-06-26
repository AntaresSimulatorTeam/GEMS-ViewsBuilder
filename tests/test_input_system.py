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


def test_locating_function_zero_peers_raises(test_dataset_dir: Path) -> None:
    """A single location port with no connected peer is an error (must be unique)."""
    system = load_system(test_dataset_dir)

    assert len(system.components) > 0
    any_component_id = system.components[0].id
    # A port that is wired to nothing has zero peers, which is not a unique location.
    with pytest.raises(ValueError):
        system.get_location(any_component_id, "this_port_is_not_connected_to_anything")
