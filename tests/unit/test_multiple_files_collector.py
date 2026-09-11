# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest

from gems_views_builder.multiple_files_collector import MultipleFilesCollector

TABLE_FILES = ("st-x-mc-1.parquet", "st-x-mc-2.parquet", "st-x-mc-3.parquet")
UNRELATED_FILE = "unrelated.txt"


@pytest.mark.parametrize(
    ("global_pattern", "expected_file_names"),
    [
        ("st-x-mc-*.parquet", set(TABLE_FILES)),
        ("st-x-mc-*", set(TABLE_FILES)),
        ("st*", set(TABLE_FILES)),
        ("*", set(TABLE_FILES) | {UNRELATED_FILE}),
    ],
)
def test_collect_returns_all_files_matching_the_glob_pattern(
    tmp_path: Path, global_pattern: str, expected_file_names: set[str]
) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    for name in (*TABLE_FILES, UNRELATED_FILE):
        (dataset_dir / name).touch()

    # Act
    collected = MultipleFilesCollector(str(dataset_dir / global_pattern)).collect()

    # Assert
    assert set(collected) == {dataset_dir / name for name in expected_file_names}


def test_collect_raises_file_not_found_error_when_no_files_match(tmp_path: Path) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="No files matched global pattern"):
        MultipleFilesCollector(str(dataset_dir / "simulation_table*.parquet")).collect()
