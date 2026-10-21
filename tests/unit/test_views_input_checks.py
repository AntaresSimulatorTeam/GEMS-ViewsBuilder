# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Tests for ``InputPathsValidator.validate()``."""

from argparse import Namespace
from pathlib import Path

import pytest

from gems_views_builder.input_paths import InputPaths
from gems_views_builder.validation.input_paths_validator import InputPathsValidator


def write_minimal_input_data_set(root: Path, library_files: list[str], catalog_files: list[str]) -> InputPaths:
    for directory, names in ((root / "libraries", library_files), (root / "catalogs", catalog_files)):
        directory.mkdir()
        for name in names:
            (directory / name).touch()

    system = root / "system.yml"
    calendar = root / "calendar.csv"
    taxonomy = root / "taxonomy.yml"
    view_config = root / "view_config.yml"
    simulation_table = root / "simulation_table.parquet"
    for path in (system, calendar, taxonomy, view_config, simulation_table):
        path.touch()

    return InputPaths(
        Namespace(
            libraries_dir=root / "libraries",
            catalogs_dir=root / "catalogs",
            system=system,
            calendar=calendar,
            taxonomy=taxonomy,
            view_configs=str(view_config),
            simulation_tables=str(simulation_table),
        )
    )


def test_validate_passes_for_minimal_valid_paths(tmp_path: Path) -> None:
    InputPathsValidator(write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])).validate()


def test_non_yml_library_files_are_not_collected(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml", "readme.txt"], ["catalog.yml"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert {path.name for path in input_paths.libraries} == {"library.yml"}


def test_validate_passes_with_multiple_model_libraries(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml", "other.yml"], ["catalog.yml"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert {path.name for path in input_paths.libraries} == {"library.yml", "other.yml"}


def test_validate_passes_with_arbitrarily_named_model_library_file(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["any_name.yml"], ["catalog.yml"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert [path.name for path in input_paths.libraries] == ["any_name.yml"]


def test_non_yml_catalog_files_are_not_collected(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml", "notes.txt"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert {path.name for path in input_paths.catalogs} == {"catalog.yml"}


def test_validate_passes_with_multiple_catalogs(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml", "other.yml"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert {path.name for path in input_paths.catalogs} == {"catalog.yml", "other.yml"}


def test_validate_passes_with_arbitrarily_named_catalog_file(tmp_path: Path) -> None:
    # Arrange
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["any_name.yml"])

    # Act
    InputPathsValidator(input_paths).validate()

    # Assert
    assert [path.name for path in input_paths.catalogs] == ["any_name.yml"]


def test_validate_raises_when_system_has_wrong_extension(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.system = tmp_path / "system.yaml"
    with pytest.raises(ValueError, match="System file"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_calendar_has_wrong_extension(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.calendar = tmp_path / "calendar.txt"
    with pytest.raises(ValueError, match="Calendar file"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_taxonomy_has_wrong_extension(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.taxonomy = tmp_path / "taxonomy.txt"
    with pytest.raises(ValueError, match="Taxonomy file"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_view_config_has_wrong_extension(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.view_configs = [tmp_path / "view_config.json"]
    with pytest.raises(ValueError, match="View config file"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_simulation_table_has_wrong_extension(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.simulation_tables = [tmp_path / "simulation_table.xls"]
    with pytest.raises(ValueError, match="Simulation table"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_simulation_tables_are_missing(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.simulation_tables = []
    with pytest.raises(ValueError, match="Simulation table files are required"):
        InputPathsValidator(input_paths).validate()


def test_validate_raises_when_simulation_tables_have_different_extensions(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    input_paths.simulation_tables = [tmp_path / "simulation_table.csv", tmp_path / "simulation_table.parquet"]
    with pytest.raises(ValueError, match="Simulation table files must have the same extension"):
        InputPathsValidator(input_paths).validate()


def test_validate_passes_when_simulation_table_is_csv(tmp_path: Path) -> None:
    input_paths = write_minimal_input_data_set(tmp_path, ["library.yml"], ["catalog.yml"])
    csv_table = tmp_path / "simulation_table.csv"
    csv_table.touch()
    input_paths.simulation_tables = [csv_table]
    InputPathsValidator(input_paths).validate()
