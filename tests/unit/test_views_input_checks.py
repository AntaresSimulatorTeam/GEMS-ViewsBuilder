# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Tests for ``StudyLayoutValidator.validate()`` (required layout under ``input_data_path``)."""

import shutil
from pathlib import Path

import pytest

from gems_views_builder.validation.study_layout_validator import EXACT_FILES, StudyLayoutValidator


def _write_minimal_valid_input_data(root: Path) -> None:
    """Everything ``StudyLayoutValidator.validate()`` expects: directory, catalogs, YAML set, calendar, simulation table."""
    catalogs = root / "catalogs"
    catalogs.mkdir(parents=True)
    (catalogs / "placeholder.yml").touch()
    for name in EXACT_FILES:
        (root / name).touch()
    (root / "calendar.csv").touch()
    (root / "simulation_table.parquet").touch()


def test_validate_passes_for_minimal_valid_layout(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_exact_file_missing(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "taxonomy.yml").unlink()
    with pytest.raises(FileNotFoundError, match="taxonomy.yml"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_calendar_missing(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "calendar.csv").unlink()
    with pytest.raises(FileNotFoundError, match="calendar"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_calendar_has_wrong_suffix(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "calendar.csv").unlink()
    (tmp_path / "calendar.txt").touch()
    with pytest.raises(ValueError, match="must be a '.csv' file"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_simulation_table_missing(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "simulation_table.parquet").unlink()
    with pytest.raises(FileNotFoundError, match="simulation_table"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_simulation_table_has_wrong_suffix(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "simulation_table.parquet").unlink()
    (tmp_path / "simulation_table.txt").touch()
    with pytest.raises(ValueError, match=r"must be a '.parquet' or '.csv' file"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_passes_when_simulation_table_is_csv(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "simulation_table.parquet").unlink()
    (tmp_path / "simulation_table.csv").touch()
    StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_catalogs_directory_missing(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    shutil.rmtree(tmp_path / "catalogs")
    with pytest.raises(NotADirectoryError, match="catalogs"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_catalogs_directory_empty(tmp_path: Path) -> None:
    _write_minimal_valid_input_data(tmp_path)
    (tmp_path / "catalogs" / "placeholder.yml").unlink()
    with pytest.raises(FileNotFoundError, match="empty"):
        StudyLayoutValidator(tmp_path).validate()


def test_validate_raises_when_input_path_is_not_a_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not_a_directory"
    file_path.touch()
    with pytest.raises(NotADirectoryError, match="not a directory"):
        StudyLayoutValidator(file_path).validate()
