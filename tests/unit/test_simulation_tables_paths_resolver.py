# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Tests for ``SimulationTablesPathsResolver.resolve()``, which turns the ``--simulation-tables``
glob pattern into the concrete list of files that will be loaded."""

from pathlib import Path

import pytest

from gems_views_builder.input_paths import SimulationTablesPathsResolver

@pytest.mark.parametrize("pattern", ["simulation_table-*.parquet", "s*.parquet"])
def test_resolve_returns_all_files_matching_the_glob_pattern(tmp_path: Path,pattern: str) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    expected_files = {
        dataset_dir / "simulation_table-1.parquet",
        dataset_dir / "simulation_table-2.parquet",
        dataset_dir / "simulation_table-3.parquet",
    }
    for file_path in expected_files:
        file_path.touch()
    (dataset_dir / "unrelated.txt").touch()

    # Act
    resolved_pattern = SimulationTablesPathsResolver(str(dataset_dir / pattern)).resolve()

    # Assert
    assert set(resolved_pattern) == expected_files


def test_resolve_raises_not_a_directory_error_when_directory_is_missing(tmp_path: Path) -> None:
    # Arrange
    missing_dir = tmp_path / "does_not_exist"

    # Act & Assert
    with pytest.raises(NotADirectoryError, match="Simulation tables directory does not exist"):
        SimulationTablesPathsResolver(str(missing_dir / "simulation_table*.parquet")).resolve()


def test_resolve_returns_empty_list_when_pattern_matches_no_file(tmp_path: Path) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    (dataset_dir / "unrelated.txt").touch()

    # Act
    resolved_paths = SimulationTablesPathsResolver(str(dataset_dir / "simulation_table*.parquet")).resolve()

    # Assert
    assert resolved_paths == []
