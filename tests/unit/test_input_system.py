# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import yaml
from gems_craft.study.parsing import SystemSchema, parse_yaml_system  # type: ignore

from gems_views_builder.input.library import load_yml_libs
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
    system = load_system(test_dataset_dir / "system.yml", load_yml_libs(library_dir))
    assert len(system.components) > 0
    assert isinstance(system.connections, list)


def test_load_system_tolerates_missing_component_parameters(test_dataset_dir: Path, tmp_path: Path) -> None:
    yml_system = yaml.safe_load((test_dataset_dir / "system.yml").read_text(encoding="utf-8"))
    for component in yml_system["system"]["components"]:
        component.pop("parameters", None)

    system_missing_params_file = tmp_path / "sys_with_missing_parameters.yml"
    system_missing_params_file.write_text(yaml.safe_dump(yml_system), encoding="utf-8")

    yml_libs = load_yml_libs(test_dataset_dir / "libraries")
    system = load_system(test_dataset_dir / "system.yml", yml_libs)
    system_with_missing_parameters = load_system(system_missing_params_file, yml_libs)

    assert {c.id for c in system_with_missing_parameters.components} == {c.id for c in system.components}
    assert len(system_with_missing_parameters.connections) == len(system.connections)
