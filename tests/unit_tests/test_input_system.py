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

TEST_FILES_ROOT = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files"

# Exact relative paths that must exist in every input_* directory.
REQUIRED_FILES = [
    "view_config.yml",
    "taxonomy.yml",
]

# Catalogs dir must exist and contain at least one .yml file (catalog.yml or catalog_1.yml, etc.)
CATALOGS_DIR = "catalogs"


def test_input_folders_have_required_files() -> None:
    """Every input_* directory must contain the required files and at least one catalog."""
    input_dirs = sorted(p for p in TEST_FILES_ROOT.iterdir() if p.is_dir() and p.name.startswith("input_"))
    for input_dir in input_dirs:
        for rel in REQUIRED_FILES:
            path = input_dir / rel
            assert path.is_file(), f"Missing required file in {input_dir.name}: {rel}"
        catalogs_path = input_dir / CATALOGS_DIR
        assert catalogs_path.is_dir(), f"Missing catalogs directory in {input_dir.name}"
        catalog_files = list(catalogs_path.glob("*.yml"))
        assert len(catalog_files) > 0, f"No catalog .yml file in {input_dir.name}/{CATALOGS_DIR}"


@pytest.mark.parametrize(
    "input_system_path",
    [
        TEST_FILES_ROOT / "test_3" / "system.yml",
    ],
)
def test_input_system_using(input_system_path: Path) -> None:
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path) as file:
        input_system = parse_yaml_components(file)
    assert input_system is not None
    assert isinstance(input_system, InputSystem)


def test_locating_function() -> None:
    """LOCATING_FUNCTION: None -> component_id, string -> peer id, tuple -> tuple of peer ids."""
    from gems_views_builder import InputSystem as GemsViewsInputSystem

    system_path = TEST_FILES_ROOT / "test_3" / "system.yml"
    assert system_path.exists(), f"System file not found: {system_path}"
    system = GemsViewsInputSystem.from_file(system_path)

    # location_port is None -> return component_id
    assert system.get_location("generator_A1", None) == "generator_A1"

    # location_port is string -> return peer component id
    assert system.get_location("generator_A1", "p_balance_port") == "busA"
    assert system.get_location("link_link_AB", "p0_port") == "busA"
    assert system.get_location("link_link_AB", "p1_port") == "busB"

    # location_port is tuple -> return tuple of peer ids
    assert system.get_location("link_link_AB", ("p0_port", "p1_port")) == ("busA", "busB")
