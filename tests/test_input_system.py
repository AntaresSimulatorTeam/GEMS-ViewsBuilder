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

from gems.study.parsing import SystemSchema, parse_yaml_components  # type: ignore

from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system


def test_input_system_using(test_dataset_dir: Path) -> None:
    input_system_path = test_dataset_dir / "system.yml"
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path, encoding="utf-8") as f:
        input_system = parse_yaml_components(f)
    assert input_system is not None
    assert isinstance(input_system, SystemSchema)


def test_system_exposes_components_and_connections(test_dataset_dir: Path) -> None:
    system = load_system(test_dataset_dir, resolve_libraries(test_dataset_dir / "library.yml"))
    assert len(system.components) > 0
    assert isinstance(system.connections, list)
