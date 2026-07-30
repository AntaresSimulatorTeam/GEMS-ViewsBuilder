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

"""E2E test for temporal aggregation.
1. Granular timesteps spanning two calendar days collapse into two ``view_date`` buckets
   when the view is aggregated at DAY granularity, one bucket per real day -- not one
   bucket per row.
2. SUM and AVG ``time_operator`` metrics produce different values from the exact same
   granular data, and both are correct per bucket.
3. The merged result stays consistent with the pre-merge temporal views.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
from pytest import approx

from gems_views_builder.input.catalog import Metric, Term, TermsOperator, TimeOperator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.view_config import TimeAggregation, ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.view.view import View, accumulate_on_disk
from gems_views_builder.view.view_sinker import ParquetViewSinker
from tests.e2e.utils import (
    build_input_data,
    make_filtered_simulation_table,
    make_raw_component,
    run_pipeline,
)

LOCATION_TAXONOMY_CATEGORY = "production"
MODEL_ID = "bus"
TAXONOMY_CATEGORY_BY_MODEL = {MODEL_ID: LOCATION_TAXONOMY_CATEGORY}


# Four granular timesteps for busA, spread across two calendar days: two per day.
DAY_1 = datetime(2026, 1, 1)
DAY_2 = datetime(2026, 1, 2)
ROWS = [
    ("busA", "active_load", 0, datetime(2026, 1, 1, 3, 0), 10.0),
    ("busA", "active_load", 0, datetime(2026, 1, 1, 20, 0), 20.0),
    ("busA", "active_load", 0, datetime(2026, 1, 2, 3, 0), 100.0),
    ("busA", "active_load", 0, datetime(2026, 1, 2, 20, 0), 200.0),
]

# LOAD_SUM per day: day1 = 10+20 = 30, day2 = 100+200 = 300.
EXPECTED_LOAD_SUM_BY_DAY = {DAY_1: 30.0, DAY_2: 300.0}
# LOAD_AVG per day: day1 = mean(10,20) = 15, day2 = mean(100,200) = 150.
EXPECTED_LOAD_AVG_BY_DAY = {DAY_1: 15.0, DAY_2: 150.0}


def build_pipeline(tmp_path: Path) -> tuple[list[MetricView], ViewConfig]:
    raw_components: list[Any] = [make_raw_component("busA", "lib." + MODEL_ID, {})]

    # Same term/output for both metrics, only the time_operator differs, isolating the
    # temporal-aggregation behavior from any spatial/terms concern.
    load_sum_metric = Metric(
        id="LOAD_SUM",
        terms=[Term(taxonomy_category=LOCATION_TAXONOMY_CATEGORY, output_id="active_load", location_port=None)],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    load_avg_metric = Metric(
        id="LOAD_AVG",
        terms=[Term(taxonomy_category=LOCATION_TAXONOMY_CATEGORY, output_id="active_load", location_port=None)],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.AVG,
    )
    metrics = [load_sum_metric, load_avg_metric]

    filtered_st = make_filtered_simulation_table(ROWS, tmp_path)

    view_config = ViewConfig(
        id="view_time",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category=LOCATION_TAXONOMY_CATEGORY,
        catalog_ids=set(),  # keeps validate_catalogs_against_taxonomy disk-free (no catalogs to load)
        time_aggregation=TimeAggregation.DAY,
        extra_locations=[],
        metric_ids=["catalog.LOAD_SUM", "catalog.LOAD_AVG"],
        metrics=metrics,
    )

    input_data: InputData = build_input_data(
        tmp_path, raw_components, [], TAXONOMY_CATEGORY_BY_MODEL, view_config, filtered_st
    )
    temporal_views = run_pipeline(input_data, tmp_path)
    return temporal_views, view_config


def values_by_day(path: Path) -> dict[datetime, float]:
    df = pl.read_parquet(path)
    return dict(zip(df["view_date"].to_list(), df["metric_value"].to_list()))


def test_granular_timesteps_are_bucketed_by_calendar_day(tmp_path: Path) -> None:
    # Arrange / Act
    temporal_views, _ = build_pipeline(tmp_path)
    load_sum_view, load_avg_view = temporal_views

    # Assert: 4 granular rows collapse into exactly 2 day-buckets, not 4 (one per row) or 1
    # (all merged together) -- each metric gets one row per real day.
    load_sum_df = pl.read_parquet(load_sum_view.persistence_path)
    load_avg_df = pl.read_parquet(load_avg_view.persistence_path)
    assert load_sum_df.shape[0] == 2
    assert load_avg_df.shape[0] == 2
    assert set(load_sum_df["view_date"].to_list()) == {DAY_1, DAY_2}
    assert set(load_avg_df["view_date"].to_list()) == {DAY_1, DAY_2}


def test_sum_and_avg_time_operators_diverge_on_the_same_granular_data(tmp_path: Path) -> None:
    # Arrange / Act
    temporal_views, _ = build_pipeline(tmp_path)
    load_sum_view, load_avg_view = temporal_views

    # Assert: LOAD_SUM and LOAD_AVG read the exact same granular rows, but produce
    # different per-day values -- confirms the time_operator, not the data, drives the split.
    load_sum_by_day = values_by_day(load_sum_view.persistence_path)
    load_avg_by_day = values_by_day(load_avg_view.persistence_path)
    for day, expected_value in EXPECTED_LOAD_SUM_BY_DAY.items():
        assert load_sum_by_day[day] == approx(expected_value)
    for day, expected_value in EXPECTED_LOAD_AVG_BY_DAY.items():
        assert load_avg_by_day[day] == approx(expected_value)


def test_merged_view_is_consistent_with_pre_merge_temporal_views(tmp_path: Path) -> None:
    # Arrange
    temporal_views, _ = build_pipeline(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Act
    view: View = accumulate_on_disk(temporal_views, ParquetViewSinker(results_dir))
    merged = view.dataframe.collect()

    # Assert: row count matches the sum of the pre-merge views (2 days x 2 metrics = 4).
    pre_merge_row_counts = [pl.read_parquet(v.persistence_path).shape[0] for v in temporal_views]
    assert merged.shape[0] == sum(pre_merge_row_counts) == 4

    for metric_id, expected_by_day in (("LOAD_SUM", EXPECTED_LOAD_SUM_BY_DAY), ("LOAD_AVG", EXPECTED_LOAD_AVG_BY_DAY)):
        rows = merged.filter(pl.col("metric_id") == metric_id)
        by_day = dict(zip(rows["view_date"].to_list(), rows["metric_value"].to_list()))
        assert set(by_day) == set(expected_by_day)
        for day, expected_value in expected_by_day.items():
            assert by_day[day] == approx(expected_value)
