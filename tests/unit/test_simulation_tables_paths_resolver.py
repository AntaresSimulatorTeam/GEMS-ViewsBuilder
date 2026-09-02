# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest

from gems_views_builder.input_paths import SimulationTablesPathsResolver

TABLE_FILES = ("st-x-mc-1.parquet", "st-x-mc-2.parquet", "st-x-mc-3.parquet")
UNRELATED_FILE = "unrelated.txt"


@pytest.mark.parametrize(
    ("pattern", "expected_file_names"),
    [
        ("st-x-mc-*.parquet", set(TABLE_FILES)),
        ("st-x-mc-*", set(TABLE_FILES)),
        ("st*", set(TABLE_FILES)),
        ("*", set(TABLE_FILES) | {UNRELATED_FILE}),
        ("lib*", set()),
    ],
)
def test_resolve_returns_all_files_matching_the_glob_pattern(
    tmp_path: Path, pattern: str, expected_file_names: set[str]
) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    for name in (*TABLE_FILES, UNRELATED_FILE):
        (dataset_dir / name).touch()

    # Act
    resolved_pattern = SimulationTablesPathsResolver(str(dataset_dir / pattern)).resolve()

    # Assert
    assert set(resolved_pattern) == {dataset_dir / name for name in expected_file_names}


def test_resolve_raises_not_a_directory_error_when_directory_is_missing(tmp_path: Path) -> None:
    # Arrange
    missing_dir = tmp_path / "does_not_exist"

    # Act & Assert
    with pytest.raises(NotADirectoryError, match="Simulation tables directory does not exist"):
        SimulationTablesPathsResolver(str(missing_dir / "simulation_table*.parquet")).resolve()
