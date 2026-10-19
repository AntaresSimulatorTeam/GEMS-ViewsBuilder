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
    ids=["current-folder", "dot-slash", "parent-folder"],
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
    # The CLI check ignores file extensions, so both options can share the same pattern
    args = Namespace(simulation_tables=global_pattern, catalogs=global_pattern)

    # Act
    check_multiple_file_path_options(args)
    collected = MultipleFilesCollector(global_pattern).collect()

    # Assert
    assert {path.resolve() for path in collected} == {(dataset_dir / name).resolve() for name in TABLE_FILES}


@pytest.mark.parametrize("option_name", ["simulation-tables", "catalogs"])
@pytest.mark.parametrize(
    ("global_pattern", "expected_error"),
    [
        ("", "does not end with a file name pattern"),
        (".", "does not end with a file name pattern"),
        ("missing/st-x-mc-*.parquet", "is not a directory"),
    ],
    ids=["empty", "dot", "missing-parent"],
)
def test_invalid_multiple_file_path_option_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, option_name: str, global_pattern: str, expected_error: str
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    args = Namespace(simulation_tables="*.parquet", catalogs="*.yml")
    setattr(args, option_name.replace("-", "_"), global_pattern)

    # Act & Assert
    with pytest.raises(OSError, match=f"--{option_name} : .*{expected_error}"):
        check_multiple_file_path_options(args)
