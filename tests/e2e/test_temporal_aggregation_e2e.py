# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""E2E test for temporal aggregation.
The merged result stays consistent with the pre-merge temporal views.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

from gems_views_builder.__main__ import build_metric_views
from gems_views_builder.input.catalog import AggregOperatorType, Metric, Term
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.view_config import TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.view.view import accumulate_on_disk
from gems_views_builder.view.view_sinker import ParquetViewSinker
from tests.e2e.utils import (
    build_input_data,
    fetch_view,
    make_filtered_simulation_table,
    make_raw_component,
    make_results_dir,
)

LOCATION_TAXONOMY_CATEGORY = "production"
MODEL_ID = "bus"
TAXONOMY_CATEGORY_BY_MODEL = {MODEL_ID: LOCATION_TAXONOMY_CATEGORY}

DAY_1 = datetime(2026, 1, 1)
DAY_2 = datetime(2026, 1, 2)
ROWS = [
    ("busA", "active_load", 0, datetime(2026, 1, 1, 3, 0), 10.0),
    ("busA", "active_load", 0, datetime(2026, 1, 1, 20, 0), 20.0),
    ("busA", "active_load", 0, datetime(2026, 1, 2, 3, 0), 100.0),
    ("busA", "active_load", 0, datetime(2026, 1, 2, 20, 0), 200.0),
]

EXPECTED_LOAD_SUM_BY_DAY = {DAY_1: 30.0, DAY_2: 300.0}
EXPECTED_LOAD_AVG_BY_DAY = {DAY_1: 15.0, DAY_2: 150.0}


def build_input(tmp_path: Path) -> InputData:
    raw_components: list[Any] = [make_raw_component("busA", "lib." + MODEL_ID, {})]

    load_sum_metric = Metric(
        id="LOAD_SUM",
        terms=[Term(taxonomy_category=LOCATION_TAXONOMY_CATEGORY, output_id="active_load", location_port=None)],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
    )
    load_avg_metric = Metric(
        id="LOAD_AVG",
        terms=[Term(taxonomy_category=LOCATION_TAXONOMY_CATEGORY, output_id="active_load", location_port=None)],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.AVG,
    )

    view_config = ViewConfig(
        id="view_time",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category=LOCATION_TAXONOMY_CATEGORY,
        catalog_ids=set(),
        time_aggregation=TimeGranularity.DAY,
        extra_locations=[],
        metric_ids=["catalog.LOAD_SUM", "catalog.LOAD_AVG"],
        metrics=[load_sum_metric, load_avg_metric],
    )
    return build_input_data(
        tmp_path,
        raw_components,
        [],
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        make_filtered_simulation_table(ROWS, tmp_path),
    )


def values_by_day(path: Path) -> dict[datetime, float]:
    df = pl.read_parquet(path)
    return dict(zip(df["view_date"].to_list(), df["metric_value"].to_list()))


def pre_merge_row_count(metric_views: list[MetricView]) -> int:
    return sum(pl.read_parquet(v.persistence_path).shape[0] for v in metric_views)


def get_metric_values_by_day(view: pl.DataFrame, metric_id: str) -> dict[datetime, float]:
    rows = view.filter(pl.col("metric_id") == metric_id)
    return dict(zip(rows["view_date"].to_list(), rows["metric_value"].to_list()))


def test_merged_view_is_consistent_with_pre_merge_temporal_views(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)
    results_dir = make_results_dir(tmp_path)

    # Act
    metric_views = build_metric_views(input_data)
    accumulate_on_disk(metric_views, ParquetViewSinker(results_dir))

    # Assert
    view = fetch_view(results_dir)
    assert view.shape[0] == pre_merge_row_count(metric_views) == 4

    for metric_id, expected_by_day in (("LOAD_SUM", EXPECTED_LOAD_SUM_BY_DAY), ("LOAD_AVG", EXPECTED_LOAD_AVG_BY_DAY)):
        by_day = get_metric_values_by_day(view, metric_id)
        for day, expected_value in expected_by_day.items():
            assert by_day[day] == expected_value
