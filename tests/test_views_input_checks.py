# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path

import pytest

from gems_views_builder.views import EXACT_FILES, ViewBuilder


def _builder_without_init(input_data_path: Path) -> ViewBuilder:
    """ViewBuilder whose input checks can be invoked without loading YAML/parquet."""
    vb = object.__new__(ViewBuilder)
    vb.input_data_path = input_data_path
    return vb


def _touch_required_six_files(base: Path) -> None:
    for name in EXACT_FILES:
        (base / name).touch()
    (base / "calendar.csv").touch()
    (base / "simulation_table.parquet").touch()


def test_check_number_of_required_files_passes_with_exactly_six_files(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    _builder_without_init(tmp_path)._check_number_of_required_files()


def test_check_number_of_required_files_passes_with_six_files_and_extra_directory(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "catalogs").mkdir()
    _builder_without_init(tmp_path)._check_number_of_required_files()


def test_check_number_of_required_files_raises_when_five_files(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "taxonomy.yml").unlink()
    with pytest.raises(ValueError, match="Expected 6 files"):
        _builder_without_init(tmp_path)._check_number_of_required_files()


def test_check_number_of_required_files_raises_when_seven_files(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "extra.yml").touch()
    with pytest.raises(ValueError, match="Expected 6 files"):
        _builder_without_init(tmp_path)._check_number_of_required_files()


def test_check_required_input_files_passes_when_layout_valid(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    _builder_without_init(tmp_path)._check_required_input_files()


def test_check_required_input_files_raises_when_exact_file_missing(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "taxonomy.yml").unlink()
    with pytest.raises(FileNotFoundError, match="taxonomy.yml"):
        _builder_without_init(tmp_path)._check_required_input_files()


def test_check_required_input_files_raises_when_prefix_file_missing(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "calendar.csv").unlink()
    with pytest.raises(FileNotFoundError, match="calendar"):
        _builder_without_init(tmp_path)._check_required_input_files()


def test_check_required_input_files_raises_when_wrong_suffix_for_prefix_match(tmp_path: Path) -> None:
    _touch_required_six_files(tmp_path)
    (tmp_path / "calendar.csv").unlink()
    (tmp_path / "calendar.txt").touch()
    with pytest.raises(ValueError, match="must be a '.csv' file"):
        _builder_without_init(tmp_path)._check_required_input_files()
