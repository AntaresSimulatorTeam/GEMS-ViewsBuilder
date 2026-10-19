# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from argparse import Namespace
from pathlib import Path

import pytest

from gems_views_builder.cli import check_multiple_file_path_options
from gems_views_builder.multiple_files_collector import MultipleFilesCollector


@pytest.mark.parametrize("global_pattern", ["st-x-mc-*.parquet", "./st-x-mc-*.parquet"])
def test_simulation_tables_in_current_directory_are_accepted_and_collected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, global_pattern: str
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    (tmp_path / "st-x-mc-1.parquet").touch()
    (tmp_path / "st-x-mc-2.parquet").touch()
    args = Namespace(simulation_tables=global_pattern, catalogs=global_pattern)

    # Act
    check_multiple_file_path_options(args)
    collected = MultipleFilesCollector(global_pattern).collect()

    # Assert
    assert set(collected) == {Path("st-x-mc-1.parquet"), Path("st-x-mc-2.parquet")}


def test_multiple_file_path_option_with_missing_parent_directory_is_rejected(tmp_path: Path) -> None:
    # Arrange
    global_pattern = str(tmp_path / "missing" / "st-x-mc-*.parquet")
    args = Namespace(simulation_tables=global_pattern, catalogs=str(tmp_path / "*.yml"))

    # Act & Assert
    with pytest.raises(OSError, match="--simulation-tables .* is not a directory"):
        check_multiple_file_path_options(args)
