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

from datetime import datetime
from pathlib import Path
from typing import cast

import polars as pl
import pytest
from pytest import approx

from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
from gems_views_builder.input.view_config import TimeAggregation
from gems_views_builder.metric_view import MetricView
from gems_views_builder.time_aggregator import (
    TimeAggregator,
    granular_date_expression,
    time_aggregation_expression,
)


def apply_date_expr(date: datetime, aggregation: TimeAggregation | None) -> datetime:
    df = pl.DataFrame({"granular_date": [date]}, schema={"granular_date": pl.Datetime})
    return cast(datetime, df.select(granular_date_expression(aggregation)).item())


def apply_agg_expr(values: list[float], time_operator: TimeOperator) -> float:
    df = pl.DataFrame({"granular_metric_value": values})
    return float(df.select(time_aggregation_expression(time_operator)).item())


def make_metric_view(rows: list[tuple[datetime, float]], tmp_path: Path) -> MetricView:
    """Granular metric-view parquet (output of the terms aggregation step)."""
    n = len(rows)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": ["L"] * n,
            "breakdown_properties": [""] * n,
            "absolute_time_index": list(range(1, n + 1)),
            "scenario": [0] * n,
            "granular_metric_value": [value for _, value in rows],
            "granular_date": [date for date, _ in rows],
        },
        schema_overrides={"granular_date": pl.Datetime},
    )
    path = tmp_path / "granular.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def make_metric(time_operator: TimeOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=TermsOperator.SUM, time_operator=time_operator)


@pytest.mark.parametrize(
    ("aggregation", "input_date", "expected_date"),
    [
        (TimeAggregation.HOUR, datetime(2026, 1, 1, 3, 30), datetime(2026, 1, 1, 3, 0)),
        (TimeAggregation.DAY, datetime(2026, 1, 1, 20, 0), datetime(2026, 1, 1, 0, 0)),
        (TimeAggregation.MONTH, datetime(2026, 1, 15, 10, 0), datetime(2026, 1, 1, 0, 0)),
        (TimeAggregation.YEAR, datetime(2026, 3, 15, 10, 0), datetime(2026, 1, 1, 0, 0)),
        (None, datetime(2026, 1, 1, 3, 0), datetime(2026, 1, 1, 3, 0)),
    ],
)
def test_granular_date_expression(
    aggregation: TimeAggregation | None,
    input_date: datetime,
    expected_date: datetime,
) -> None:
    assert apply_date_expr(input_date, aggregation) == expected_date


@pytest.mark.parametrize(
    ("time_operator", "values", "expected"),
    [
        (TimeOperator.SUM, [10.0, 20.0], 30.0),
        (TimeOperator.AVG, [10.0, 20.0], 15.0),
    ],
)
def test_time_aggregation_expression(time_operator: TimeOperator, values: list[float], expected: float) -> None:
    assert apply_agg_expr(values, time_operator) == approx(expected)


def test_truncation_groups_by_window(tmp_path: Path) -> None:
    # Arrange
    aggregator = TimeAggregator(TimeAggregation.DAY)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]
    metric_view = make_metric_view(rows, tmp_path)
    metric = make_metric(TimeOperator.SUM)

    # Act
    out_metric_view = aggregator.run(metric_view, metric)

    # Assert
    df = pl.read_parquet(out_metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["view_date"][0] == datetime(2026, 1, 1, 0, 0)
    assert df["metric_value"][0] == approx(30.0)
    assert df["metric_value"].dtype == pl.Float64


def test_no_truncation_keeps_granular_dates(tmp_path: Path) -> None:
    # Arrange
    aggregator = TimeAggregator(None)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]
    metric_view = make_metric_view(rows, tmp_path)
    metric = make_metric(TimeOperator.SUM)

    # Act
    out_metric_view = aggregator.run(metric_view, metric)

    # Assert
    df = pl.read_parquet(out_metric_view.persistence_path).sort("view_date")
    assert df["view_date"].to_list() == [datetime(2026, 1, 1, 3, 0), datetime(2026, 1, 1, 20, 0)]
    assert df["metric_value"].to_list() == [approx(10.0), approx(20.0)]


def test_temporal_aggregation_avg(tmp_path: Path) -> None:
    # Arrange
    aggregator = TimeAggregator(TimeAggregation.DAY)
    rows = [(datetime(2026, 1, 1, 1, 0), 10.0), (datetime(2026, 1, 1, 2, 0), 20.0)]
    metric_view = make_metric_view(rows, tmp_path)
    metric = make_metric(TimeOperator.AVG)

    # Act
    out_metric_view = aggregator.run(metric_view, metric)

    # Assert
    df = pl.read_parquet(out_metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["view_date"][0] == datetime(2026, 1, 1, 0, 0)
    assert df["metric_value"][0] == approx(15.0)  # mean(10.0, 20.0)


def test_part_counter_increments_file_names(tmp_path: Path) -> None:
    # Arrange
    aggregator = TimeAggregator(TimeAggregation.DAY)
    metric = make_metric(TimeOperator.SUM)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]
    metric_view = make_metric_view(rows, tmp_path)

    # Act
    first = aggregator.run(metric_view, metric)
    second = aggregator.run(make_metric_view(rows, tmp_path), metric)

    # Assert
    assert first.persistence_path != second.persistence_path
    assert first.persistence_path.name.endswith("-0.parquet")
    assert second.persistence_path.name.endswith("-1.parquet")

    # Each part is truncated to its day and the two intra-day values are summed.
    for part in (first, second):
        df = pl.read_parquet(part.persistence_path)
        assert df.shape[0] == 1
        assert df["view_date"][0] == datetime(2026, 1, 1, 0, 0)
        assert df["metric_value"][0] == approx(30.0)
