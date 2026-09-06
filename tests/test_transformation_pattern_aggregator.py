# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.aggregators.transformation_pattern_aggregator import TransformationPatternOperator
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import TimeGranularity, TransformationPattern
from gems_views_builder.metric_view import MetricView


def make_metric_view(tmp_path: Path, location_values: list[tuple[str, float]]) -> MetricView:
    n = len(location_values)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": [location for location, _ in location_values],
            "breakdown_properties": [""] * n,
            "absolute_time_index": list(range(1, n + 1)),
            "scenario_id": [0] * n,
            "granular_metric_value": [value for _, value in location_values],
            "granular_date": [datetime(2026, 1, 1, 3, 0)] * n,
        },
        schema_overrides={"granular_date": pl.Datetime},
    )
    path = tmp_path / "granular.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def make_metric() -> Metric:
    return Metric(id="M", terms=[], terms_operator=AggregOperatorType.SUM, time_operator=AggregOperatorType.SUM)


def make_pattern(scenario: bool, spatial_filter: list[str] | None) -> TransformationPattern:
    return TransformationPattern(
        id="hourly",
        time_granularity=TimeGranularity.HOUR,
        scenario=scenario,
        spatial_filter=spatial_filter,
    )


@pytest.mark.parametrize(
    ("scenario", "spatial_filter", "expected_locations"),
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
    tmp_path: Path, scenario: bool, spatial_filter: list[str] | None, expected_locations: set[str]
) -> None:
    # Arrange
    metric_view = make_metric_view(tmp_path, [("busA", 100.0), ("busB", 50.0), ("busC", 999.0)])

    result = TransformationPatternOperator(make_pattern(scenario, spatial_filter)).run(metric_view, make_metric())

    df = pl.read_parquet(result.persistence_path)
    assert set(df["metric_location"].to_list()) == expected_locations
