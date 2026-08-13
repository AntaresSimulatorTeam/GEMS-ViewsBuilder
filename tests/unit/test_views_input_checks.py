# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Tests for ``InputPathsValidator.validate()``."""

from dataclasses import replace
from pathlib import Path

import pytest

from gems_views_builder.input_paths import InputPaths
from gems_views_builder.validation.input_paths_validator import InputPathsValidator


def write_minimal_paths(root: Path) -> InputPaths:
    libraries_dir = root / "libraries"
    catalogs_dir = root / "catalogs"
    libraries_dir.mkdir()
    catalogs_dir.mkdir()
    (libraries_dir / "library.yml").touch()
    (catalogs_dir / "catalog.yml").touch()

    system = root / "system.yml"
    calendar = root / "calendar.csv"
    taxonomy = root / "taxonomy.yml"
    view_config = root / "view_config.yml"
    simulation_table = root / "simulation_table.parquet"
    for path in (system, calendar, taxonomy, view_config, simulation_table):
        path.touch()

    return InputPaths(
        libraries_dir=libraries_dir,
        catalogs_dir=catalogs_dir,
        system=system,
        calendar=calendar,
        taxonomy=taxonomy,
        view_config=view_config,
        simulation_table=simulation_table,
    )


def test_validate_passes_for_minimal_valid_paths(tmp_path: Path) -> None:
    InputPathsValidator(write_minimal_paths(tmp_path)).validate()


def test_validate_raises_when_model_libraries_contain_non_yml(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    (paths.libraries_dir / "readme.txt").touch()
    with pytest.raises(ValueError, match="non-.yml"):
        InputPathsValidator(paths).validate()


def test_validate_passes_with_multiple_model_libraries(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    (paths.libraries_dir / "other.yml").touch()
    InputPathsValidator(paths).validate()


def test_validate_passes_with_arbitrarily_named_model_library_file(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    (paths.libraries_dir / "library.yml").unlink()
    (paths.libraries_dir / "any_name.yml").touch()
    InputPathsValidator(paths).validate()


def test_validate_raises_when_catalogs_contain_non_yml(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    (paths.catalogs_dir / "notes.txt").touch()
    with pytest.raises(ValueError, match="non-.yml"):
        InputPathsValidator(paths).validate()


def test_validate_passes_with_multiple_catalogs(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    (paths.catalogs_dir / "other.yml").touch()
    InputPathsValidator(paths).validate()


def test_validate_raises_when_system_has_wrong_extension(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    with pytest.raises(ValueError, match="System file"):
        InputPathsValidator(replace(paths, system=tmp_path / "system.yaml")).validate()


def test_validate_raises_when_calendar_has_wrong_extension(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    with pytest.raises(ValueError, match="Calendar file"):
        InputPathsValidator(replace(paths, calendar=tmp_path / "calendar.txt")).validate()


def test_validate_raises_when_taxonomy_has_wrong_extension(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    with pytest.raises(ValueError, match="Taxonomy file"):
        InputPathsValidator(replace(paths, taxonomy=tmp_path / "taxonomy.txt")).validate()


def test_validate_raises_when_view_config_has_wrong_extension(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    with pytest.raises(ValueError, match="View config file"):
        InputPathsValidator(replace(paths, view_config=tmp_path / "view_config.json")).validate()


def test_validate_raises_when_simulation_table_has_wrong_extension(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    with pytest.raises(ValueError, match="Simulation table"):
        InputPathsValidator(replace(paths, simulation_table=tmp_path / "simulation_table.xls")).validate()


def test_validate_passes_when_simulation_table_is_csv(tmp_path: Path) -> None:
    paths = write_minimal_paths(tmp_path)
    csv_table = tmp_path / "simulation_table.csv"
    csv_table.touch()
    InputPathsValidator(replace(paths, simulation_table=csv_table)).validate()
