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
from gems.study.parsing import InputSystem, parse_yaml_components

SYSTEMS_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files" / "systems"


@pytest.mark.parametrize(
    "input_system_path",
    [
        Path(SYSTEMS_DIR / "system_france_clusters_50_snapshots_365_period_one_year.yml"),
        Path(SYSTEMS_DIR / "system_france_clusters_80_snapshots_168_period_one_week.yml"),
    ],
)
def test_input_system_using(input_system_path: Path):
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path) as file:
        input_system = parse_yaml_components(file)
    assert input_system is not None
    assert isinstance(input_system, InputSystem)
