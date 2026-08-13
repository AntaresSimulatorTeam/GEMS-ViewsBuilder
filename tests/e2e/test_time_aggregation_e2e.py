# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import shutil
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.__main__ import load_and_validate_input_data, run_view_building_process
from gems_views_builder.input.view_config import TimeGranularity, load_view_config
from gems_views_builder.view import ParquetViewSinker
from tests.e2e.utils import fetch_view, make_results_dir

AGGREGATION_BLOCK = "  aggregations:\n    time: hour\n    scenario: false\n"


# test_3/calendar_file.csv spans 2025-01-01 00:00 .. 2025-01-01 23:00 (24 granular hours).
HOURLY_DATES = [datetime(2025, 1, 1, h) for h in range(24)]

EXPECTED_DATES_BY_AGGREGATION = {
    TimeGranularity.HOUR: HOURLY_DATES,
    TimeGranularity.DAY: [datetime(2025, 1, 1)],
    TimeGranularity.WEEK: [datetime(2024, 12, 30)],
    TimeGranularity.MONTH: [datetime(2025, 1, 1)],
    TimeGranularity.YEAR: [datetime(2025, 1, 1)],
}


def replace_aggregation(view_config_path: Path, aggregation_time: TimeGranularity) -> None:
    text = view_config_path.read_text()
    replacement = f"  aggregations:\n    time: {aggregation_time.value}\n    scenario: false\n"
    if AGGREGATION_BLOCK not in text:
        raise AssertionError(f"Expected aggregation block not found in {view_config_path}")
    view_config_path.write_text(text.replace(AGGREGATION_BLOCK, replacement))


def extract_filtered_rows_from_view(view: pl.DataFrame) -> list[datetime]:
    rows = view.filter((pl.col("metric_id") == "PROD") & (pl.col("metric_location") == "busA")).sort("view_date")
    return rows["view_date"].to_list()


@pytest.mark.parametrize("aggregation_time", list(TimeGranularity))
def test_yaml_time_aggregation_drives_full_pipeline(
    test_files_root: Path, tmp_path: Path, aggregation_time: TimeGranularity
) -> None:
    # Arrange
    dataset_dir = tmp_path / "test_3"
    shutil.copytree(test_files_root / "test_3", dataset_dir)
    replace_aggregation(dataset_dir / "view_config.yml", aggregation_time)
    results_dir = make_results_dir(tmp_path)

    # Act
    run_view_building_process(load_and_validate_input_data(dataset_dir), ParquetViewSinker(results_dir))

    # Assert
    view = fetch_view(results_dir)
    dates = extract_filtered_rows_from_view(view)
    assert dates == EXPECTED_DATES_BY_AGGREGATION[aggregation_time]


def test_yaml_missing_aggregation_key_fails_to_parse(test_files_root: Path, tmp_path: Path) -> None:
    dataset_dir = tmp_path / "test_3"
    shutil.copytree(test_files_root / "test_3", dataset_dir)
    config_path = dataset_dir / "view_config.yml"
    config_path.write_text(config_path.read_text().replace(AGGREGATION_BLOCK, ""))

    with pytest.raises(ValueError, match="aggregations"):
        load_view_config(config_path)
