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
    "catalogs/catalog_1.yml",
]


def test_input_folders_have_required_files() -> None:
    """Every input_* directory must contain the required files with exact names."""
    input_dirs = sorted(p for p in TEST_FILES_ROOT.iterdir() if p.is_dir() and p.name.startswith("input_"))
    for input_dir in input_dirs:
        for rel in REQUIRED_FILES:
            path = input_dir / rel
            assert path.is_file(), f"Missing required file in {input_dir.name}: {rel}"


@pytest.mark.parametrize(
    "input_system_path",
    [
        TEST_FILES_ROOT / "input_one_daily" / "system_france_clusters_50_snapshots_365_period_one_year.yml",
        TEST_FILES_ROOT / "input_two_hourly" / "system_france_clusters_80_snapshots_168_period_one_week.yml",
    ],
)
def test_input_system_using(input_system_path: Path) -> None:
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path) as file:
        input_system = parse_yaml_components(file)
    assert input_system is not None
    assert isinstance(input_system, InputSystem)
