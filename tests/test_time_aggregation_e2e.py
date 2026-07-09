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

"""End-to-end coverage for the `aggregation[].time` field of view_config.yml.

Unlike tests/test_time_aggregator.py (which exercises TimeAggregator directly on a
synthetic MetricView), this drives the full YAML-driven pipeline
(Loader -> ViewBuilder -> accumulate_on_disk) to confirm that the value parsed from the
YAML file actually truncates `view_date` to the expected calendar window, for every
TimeAggregation enum member plus the "not configured" case.
"""

import shutil
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.input.view_config import TimeAggregation, load_view_config
from gems_views_builder.loader import Loader
from gems_views_builder.view import accumulate_on_disk
from gems_views_builder.views_builder import ViewBuilder

AGGREGATION_BLOCK = "  aggregation:\n    - time: hour\n"

# test_3/calendar_file.csv spans 2025-01-01 01:00 .. 2025-01-02 00:00 (24 granular hours).
HOURLY_DATES = [datetime(2025, 1, 1, h) for h in range(1, 24)] + [datetime(2025, 1, 2)]

EXPECTED_DATES_BY_AGGREGATION = {
    TimeAggregation.HOUR: HOURLY_DATES,
    TimeAggregation.DAY: [datetime(2025, 1, 1), datetime(2025, 1, 2)],
    TimeAggregation.WEEK: [datetime(2024, 12, 30)],
    TimeAggregation.MONTH: [datetime(2025, 1, 1)],
    TimeAggregation.YEAR: [datetime(2025, 1, 1)],
    None: HOURLY_DATES,  # kept as-is
}


def replace_aggregation(view_config_path: Path, aggregation_time: TimeAggregation | None) -> None:
    text = view_config_path.read_text()
    replacement = (
        "  aggregation: []\n" if aggregation_time is None else f"  aggregation:\n    - time: {aggregation_time.value}\n"
    )
    view_config_path.write_text(text.replace(AGGREGATION_BLOCK, replacement))


@pytest.mark.parametrize("aggregation_time", [*TimeAggregation, None])
def test_yaml_time_aggregation_drives_full_pipeline(
    test_files_root: Path, tmp_path: Path, aggregation_time: TimeAggregation | None
) -> None:
    # Arrange, copy test_3 fixture and set aggregation to value under test
    dataset_dir = tmp_path / "test_3"
    shutil.copytree(test_files_root / "test_3", dataset_dir)
    replace_aggregation(dataset_dir / "view_config.yml", aggregation_time)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Act, run pipeline
    metric_views = ViewBuilder(Loader(dataset_dir).load()).build()
    accumulate_on_disk(metric_views, results_dir)
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
