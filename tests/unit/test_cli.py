# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from argparse import Namespace
from pathlib import Path

import pytest

from gems_views_builder.cli import check_multiple_file_path_options
from gems_views_builder.multiple_files_collector import MultipleFilesCollector

TABLE_FILES = ("st-x-mc-1.parquet", "st-x-mc-2.parquet")


@pytest.mark.parametrize(
    ("working_dir", "global_pattern"),
    [
        ("dataset", "st-x-mc-*.parquet"),
        ("dataset", "./st-x-mc-*.parquet"),
        ("dataset/sub", "../st-x-mc-*.parquet"),
    ],
)
def test_relative_multiple_file_path_options_are_accepted_and_collected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, working_dir: str, global_pattern: str
) -> None:
    # Arrange
    dataset_dir = tmp_path / "dataset"
    (dataset_dir / "sub").mkdir(parents=True)
    for name in TABLE_FILES:
        (dataset_dir / name).touch()
    monkeypatch.chdir(tmp_path / working_dir)
    args = Namespace(simulation_tables=global_pattern, catalogs=global_pattern)

    # Act
    check_multiple_file_path_options(args)
    collected = MultipleFilesCollector(global_pattern).collect()

    # Assert
    assert {path.resolve() for path in collected} == {(dataset_dir / name).resolve() for name in TABLE_FILES}


def test_multiple_file_path_option_with_missing_parent_directory_is_rejected(tmp_path: Path) -> None:
    # Arrange
    global_pattern = str(tmp_path / "missing" / "st-x-mc-*.parquet")
    args = Namespace(simulation_tables=global_pattern, catalogs=str(tmp_path / "*.yml"))

    # Act & Assert
    with pytest.raises(OSError, match="--simulation-tables .* is not a directory"):
        check_multiple_file_path_options(args)
