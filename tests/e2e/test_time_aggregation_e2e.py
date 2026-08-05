# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import shutil
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.__main__ import load_and_validate_input_data, run_view_building_process
from gems_views_builder.input.view_config import TimeAggregation, load_view_config
from gems_views_builder.view import ParquetViewSinker

AGGREGATION_BLOCK = "  aggregation:\n    time: hour\n    scenario: false\n"


# test_3/calendar_file.csv spans 2025-01-01 00:00 .. 2025-01-01 23:00 (24 granular hours).
HOURLY_DATES = [datetime(2025, 1, 1, h) for h in range(24)]

EXPECTED_DATES_BY_AGGREGATION = {
    TimeAggregation.HOUR: HOURLY_DATES,
    TimeAggregation.DAY: [datetime(2025, 1, 1)],
    TimeAggregation.WEEK: [datetime(2024, 12, 30)],
    TimeAggregation.MONTH: [datetime(2025, 1, 1)],
    TimeAggregation.YEAR: [datetime(2025, 1, 1)],
}


@pytest.mark.parametrize("aggregation_time", list(TimeAggregation))
def test_yaml_time_aggregation_drives_full_pipeline(
    test_files_root: Path, tmp_path: Path, aggregation_time: TimeAggregation
) -> None:
    # Arrange, copy test_3 fixture and set aggregation to value under test
    dataset_dir = tmp_path / "test_3"
    shutil.copytree(test_files_root / "test_3", dataset_dir)
    config_path = dataset_dir / "view_config.yml"
    config_path.write_text(
        config_path.read_text().replace(
            AGGREGATION_BLOCK,
            f"  aggregation:\n    time: {aggregation_time.value}\n    scenario: false\n",
        )
    )
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Act, run pipeline
    run_view_building_process(load_and_validate_input_data(dataset_dir), ParquetViewSinker(results_dir))
    result = pl.read_parquet(next(results_dir.glob("view*.parquet")))
    rows = result.filter((pl.col("metric_id") == "PROD") & (pl.col("metric_location") == "busA")).sort("view_date")

    # Assert, check expected result
    assert rows["view_date"].to_list() == EXPECTED_DATES_BY_AGGREGATION[aggregation_time]


def test_yaml_missing_aggregation_key_fails_to_parse(test_files_root: Path, tmp_path: Path) -> None:
    dataset_dir = tmp_path / "test_3"
    shutil.copytree(test_files_root / "test_3", dataset_dir)
    config_path = dataset_dir / "view_config.yml"
    config_path.write_text(config_path.read_text().replace(AGGREGATION_BLOCK, ""))

    with pytest.raises(ValueError, match="aggregation"):
        load_view_config(config_path)
