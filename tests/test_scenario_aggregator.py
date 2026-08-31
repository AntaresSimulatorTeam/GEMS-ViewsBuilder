# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path
from statistics import mean
from statistics import pstdev as std_deviation

import polars as pl
import pytest
from pytest import approx

from gems_views_builder.aggregators.scenario_aggregator import (
    ScenarioAggregation,
    ScenarioAggregator,
    ScenarioColumnsAddition,
    make_scenario_operator,
)
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity
from gems_views_builder.metric_view import TemporalMetricView


def make_metric() -> Metric:
    return Metric(id="M", terms=[], terms_operator=AggregOperatorType.SUM, time_operator=AggregOperatorType.SUM)


def make_pattern(scenario: bool = False, spatial_filter: list[str] | None = None) -> AggregationPattern:
    return AggregationPattern(
        id="p",
        time_granularity=TimeGranularity.HOUR,
        scenario=scenario,
        spatial_filter=spatial_filter,
    )


def make_metric_view(tmp_path: Path, location_values: list[tuple[str, float]]) -> TemporalMetricView:
    """Minimal parquet for the scenario step: metric_id, metric_location, breakdown_properties, view_date."""
    n = len(location_values)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": [location for location, _ in location_values],
            "breakdown_properties": [""] * n,
            "view_date": [datetime(2026, 1, 1)] * n,
            "scenario_id": list(range(n)),
            "metric_value": [value for _, value in location_values],
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
    return TemporalMetricView(path, TimeGranularity.HOUR)


def temporal_metric_view(tmp_path: Path, values: list[float]) -> TemporalMetricView:
    return make_metric_view(tmp_path, [("L", value) for value in values])


def test_make_scenario_operator_returns_columns_addition_when_disabled() -> None:
    assert isinstance(make_scenario_operator(False), ScenarioColumnsAddition)


def test_make_scenario_operator_returns_aggregation_when_enabled() -> None:
    assert isinstance(make_scenario_operator(True), ScenarioAggregation)


def test_to_scenario_view_with_columns_addition_preserves_rows(tmp_path: Path) -> None:
    # Arrange
    values = [10.0, 20.0, 30.0]
    metric_view = temporal_metric_view(tmp_path, values)
    original_path = metric_view.persistence_path
    aggregator = ScenarioAggregator(make_pattern(scenario=False))

    # Act
    aggregator.run(metric_view, make_metric())

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
    aggregator = ScenarioAggregator(make_pattern(scenario=True))

    # Act
    aggregator.run(metric_view, make_metric())

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


@pytest.mark.parametrize(
    ("scenario", "locations", "expected_locations"),
    [
        (True, ["busA"], {"busA"}),
        (False, ["busA"], {"busA"}),
        (True, ["busA", "busC"], {"busA", "busC"}),
        (False, ["busA", "busC"], {"busA", "busC"}),
        (True, None, {"busA", "busB", "busC"}),
        (False, None, {"busA", "busB", "busC"}),
    ],
)
def test_spatial_filter(
    tmp_path: Path, scenario: bool, locations: list[str] | None, expected_locations: set[str]
) -> None:
    # Arrange
    metric_view = make_metric_view(tmp_path, [("busA", 100.0), ("busB", 50.0), ("busC", 999.0)])
    scenario_aggregator = ScenarioAggregator(make_pattern(scenario=scenario, spatial_filter=locations))

    # Act
    scenario_aggregator.run(metric_view, make_metric())

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert set(df["metric_location"].to_list()) == expected_locations
