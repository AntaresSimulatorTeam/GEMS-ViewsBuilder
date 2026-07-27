# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Tests for ``InputLayoutValidator.validate()`` (required layout under ``input_dir``)."""

import shutil
from pathlib import Path

import pytest

from gems_views_builder.validation.study_layout_validator import InputLayoutValidator


def _write_minimal_valid_study(root: Path) -> None:
    """Everything ``InputLayoutValidator.validate()`` expects, rooted at the GVB input directory."""
    input_dir = root / "input"
    (input_dir / "model-libraries").mkdir(parents=True)
    (input_dir / "model-libraries" / "library.yml").touch()
    (input_dir / "system.yml").touch()
    (input_dir / "calendar_file.csv").touch()
    (input_dir / "catalogs").mkdir()
    (input_dir / "catalogs" / "placeholder.yml").touch()
    (input_dir / "taxonomy").mkdir()
    (input_dir / "taxonomy" / "taxonomy.yml").touch()
    (input_dir / "view-configs").mkdir()
    (input_dir / "view-configs" / "view_config.yml").touch()

    simulation_dir = root / "output" / "20260101-0000"
    simulation_dir.mkdir(parents=True)
    (simulation_dir / "simulation_table.parquet").touch()


def test_validate_passes_for_minimal_valid_layout(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_model_libraries_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    shutil.rmtree(tmp_path / "input" / "model-libraries")
    with pytest.raises(NotADirectoryError, match="model library"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_model_libraries_has_multiple_files(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "model-libraries" / "other.yml").touch()
    with pytest.raises(ValueError, match="model library"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_system_file_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "system.yml").unlink()
    with pytest.raises(FileNotFoundError, match="system.yml"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_calendar_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "calendar_file.csv").unlink()
    with pytest.raises(FileNotFoundError, match="calendar"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_catalogs_directory_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    shutil.rmtree(tmp_path / "input" / "catalogs")
    with pytest.raises(NotADirectoryError, match="Catalogs"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_catalogs_directory_empty(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "catalogs" / "placeholder.yml").unlink()
    with pytest.raises(FileNotFoundError, match="no catalog"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_passes_with_multiple_catalogs(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "catalogs" / "other.yml").touch()
    InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_taxonomy_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "taxonomy" / "taxonomy.yml").unlink()
    with pytest.raises(FileNotFoundError, match="taxonomy"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_view_config_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "input" / "view-configs" / "view_config.yml").unlink()
    with pytest.raises(FileNotFoundError, match="view config"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_output_directory_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    shutil.rmtree(tmp_path / "output")
    with pytest.raises(NotADirectoryError, match="Output directory"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_simulation_table_missing(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "output" / "20260101-0000" / "simulation_table.parquet").unlink()
    with pytest.raises(FileNotFoundError, match="simulation_table"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_passes_when_simulation_table_is_csv(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    (tmp_path / "output" / "20260101-0000" / "simulation_table.parquet").unlink()
    (tmp_path / "output" / "20260101-0000" / "simulation_table.csv").touch()
    InputLayoutValidator(tmp_path).validate()


def test_validate_picks_most_recent_simulation_folder_by_name(tmp_path: Path) -> None:
    _write_minimal_valid_study(tmp_path)
    older_dir = tmp_path / "output" / "20250101-0000"
    older_dir.mkdir()
    (older_dir / "simulation_table.parquet").touch()
    # Newest folder ("20260101-0000") has a wrongly-suffixed file: it must still be the one picked
    # (and fail), proving the older folder is ignored even though it is valid.
    (tmp_path / "output" / "20260101-0000" / "simulation_table.parquet").unlink()
    (tmp_path / "output" / "20260101-0000" / "simulation_table.txt").touch()
    with pytest.raises(FileNotFoundError, match="20260101-0000"):
        InputLayoutValidator(tmp_path).validate()


def test_validate_raises_when_input_dir_is_not_a_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not_a_directory"
    file_path.touch()
    with pytest.raises(NotADirectoryError, match="not a directory"):
        InputLayoutValidator(file_path).validate()
