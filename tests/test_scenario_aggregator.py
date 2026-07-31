# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path
from statistics import mean
from statistics import pstdev as std_deviation

import polars as pl
from pytest import approx

from gems_views_builder.aggregators.scenario_aggregator import (
    ScenarioAggregation,
    ScenarioColumnsAddition,
    make_scenario_operator,
    to_scenario_view,
)
from gems_views_builder.metric_view import MetricView


def temporal_metric_view(tmp_path: Path, values: list[float]) -> MetricView:
    """Temporal aggregation-shaped parquet (input to scenario step)."""
    n = len(values)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": ["L"] * n,
            "breakdown_properties": [""] * n,
            "view_date": [datetime(2026, 1, 1)] * n,
            "scenario_id": list(range(n)),
            "metric_value": values,
        },
        schema={
            "metric_id": pl.Utf8,
            "metric_location": pl.Utf8,
            "breakdown_properties": pl.Utf8,
            "view_date": pl.Datetime,
            "scenario_id": pl.Int64,
            "metric_value": pl.Float64,
        },
    )
    path = tmp_path / "temporal.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def test_make_scenario_operator_returns_columns_addition_when_disabled() -> None:
    assert isinstance(make_scenario_operator(False), ScenarioColumnsAddition)


def test_make_scenario_operator_returns_aggregation_when_enabled() -> None:
    assert isinstance(make_scenario_operator(True), ScenarioAggregation)


def scenario_independent_temporal_metric_view(tmp_path: Path, value: float) -> MetricView:
    """Temporal aggregation-shaped parquet for a scenario-independent metric.

    A scenario-independent output already arrives as a single row with a null
    scenario_id: TermsAggregator/TimeAggregator group by scenario_id and Polars
    groups nulls together, collapsing all-null-scenario rows into one.
    """
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"],
            "metric_location": ["L"],
            "breakdown_properties": [""],
            "view_date": [datetime(2026, 1, 1)],
            "scenario_id": [None],
            "metric_value": [value],
        },
        schema={
            "metric_id": pl.Utf8,
            "metric_location": pl.Utf8,
            "breakdown_properties": pl.Utf8,
            "view_date": pl.Datetime,
            "scenario_id": pl.Int64,
            "metric_value": pl.Float64,
        },
    )
    path = tmp_path / "temporal.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def test_scenario_aggregation_false_preserves_scenario_independent_row(tmp_path: Path) -> None:
    # Arrange
    metric_view = scenario_independent_temporal_metric_view(tmp_path, value=42.0)
    original_path = metric_view.persistence_path
    aggregator = ScenarioAggregator(False)

    # Act
    aggregator.run(metric_view)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert metric_view.persistence_path == original_path
    assert df.height == 1
    assert df["scenario_id"].null_count() == 1
    assert df["scenario_aggregation"].to_list() == [False]
    assert df["scenario_stat"].null_count() == 1
    assert df["metric_value"].to_list() == [approx(42.0)]


def test_scenario_aggregation_true_scenario_independent_output_is_not_double_counted(tmp_path: Path) -> None:
    # Arrange
    metric_view = scenario_independent_temporal_metric_view(tmp_path, value=42.0)
    original_path = metric_view.persistence_path
    aggregator = ScenarioAggregator(True)

    # Act
    aggregator.run(metric_view)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert metric_view.persistence_path == original_path
    # A single scenario-independent value still yields one row per stat, not
    # one row per (scenario x stat): exp/min/max collapse to the constant
    # value and std collapses to 0, rather than being inflated or dropped.
    assert df.height == 4
    assert df["scenario_id"].null_count() == 4
    assert df["scenario_aggregation"].to_list() == [True] * 4

    by_stat = {row["scenario_stat"]: row["metric_value"] for row in df.iter_rows(named=True)}
    assert by_stat["exp"] == approx(42.0)
    assert by_stat["std"] == approx(0.0)
    assert by_stat["min"] == approx(42.0)
    assert by_stat["max"] == approx(42.0)


def test_scenario_aggregation_false_preserves_rows_and_adds_columns(tmp_path: Path) -> None:
    # Arrange
    values = [10.0, 20.0, 30.0]
    metric_view = temporal_metric_view(tmp_path, values)
    original_path = metric_view.persistence_path
    operator = make_scenario_operator(False)

    # Act
    to_scenario_view(metric_view, operator)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path).sort("scenario_id")
    assert metric_view.persistence_path == original_path
    assert "scenario_aggregation" in df.columns and "scenario_stat" in df.columns
    assert df.height == 3
    assert df["scenario_aggregation"].to_list() == [False, False, False]
    assert df["scenario_stat"].null_count() == 3
    assert df["scenario_id"].to_list() == [0, 1, 2]
    assert df["metric_value"].to_list() == [approx(10.0), approx(20.0), approx(30.0)]


def test_to_scenario_view_with_aggregation_emits_exp_std_min_max(tmp_path: Path) -> None:
    # Arrange
    values = [10.0, 20.0, 30.0]
    metric_view = temporal_metric_view(tmp_path, values)
    original_path = metric_view.persistence_path
    operator = make_scenario_operator(True)

    # Act
    to_scenario_view(metric_view, operator)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert metric_view.persistence_path == original_path
    assert df.height == 4
    assert set(df["scenario_stat"].to_list()) == {"exp", "std", "min", "max"}
    assert df["scenario_aggregation"].to_list() == [True] * 4
    assert df["scenario_id"].null_count() == 4

    stats_to_values = {row["scenario_stat"]: row["metric_value"] for row in df.iter_rows(named=True)}
    assert stats_to_values["exp"] == approx(mean(values))
    assert stats_to_values["std"] == approx(std_deviation(values))
    assert stats_to_values["min"] == approx(min(values))
    assert stats_to_values["max"] == approx(max(values))
