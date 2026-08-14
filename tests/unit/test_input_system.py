# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from gems_craft.study.parsing import SystemSchema, parse_yaml_system  # type: ignore

from gems_views_builder.input.library import load_library_schemas
from gems_views_builder.input.system import load_system


def test_input_system_using(test_dataset_dir: Path) -> None:
    input_system_path = test_dataset_dir / "system.yml"
    assert input_system_path.exists(), f"System file not found: {input_system_path}"
    with open(input_system_path, encoding="utf-8") as f:
        input_system = parse_yaml_system(f)
    assert input_system is not None
    assert isinstance(input_system, SystemSchema)


def test_system_exposes_components_and_connections(test_dataset_dir: Path) -> None:
    library_dir = test_dataset_dir / "libraries"
    system = load_system(test_dataset_dir / "system.yml", load_library_schemas(library_dir))
    assert len(system.components) > 0
    assert isinstance(system.connections, list)
