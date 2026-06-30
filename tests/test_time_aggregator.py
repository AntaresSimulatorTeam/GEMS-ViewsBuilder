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

import polars as pl
import pytest
from pytest import approx

from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
from gems_views_builder.input.view_config import TimeAggregation
from gems_views_builder.metric_view import MetricView
from gems_views_builder.time_aggregator import TimeAggregator


def _granular_view(rows: list[tuple[datetime, float]], tmp_path: Path) -> MetricView:
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


def _metric(time_operator: TimeOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=TermsOperator.SUM, time_operator=time_operator)


@pytest.mark.parametrize(
    ("aggregation", "expected_window"),
    [
        (TimeAggregation.HOUR, "1h"),
        (TimeAggregation.DAY, "1d"),
        (TimeAggregation.WEEK, "1w"),
        (TimeAggregation.MONTH, "1mo"),
        (TimeAggregation.YEAR, "1y"),
        (None, "no truncation"),
    ],
)
def test_parse_time_aggregation(aggregation: TimeAggregation | None, expected_window: str) -> None:
    assert TimeAggregator.parse_time_aggregation(aggregation) == expected_window


def test_parse_time_aggregation_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Invalid time aggregation"):
        TimeAggregator.parse_time_aggregation("decade")  # type: ignore[arg-type]


def test_truncation_groups_by_window(tmp_path: Path) -> None:
    aggregator = TimeAggregator(TimeAggregation.DAY)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]
    result = aggregator.run(_granular_view(rows, tmp_path), _metric(TimeOperator.SUM))
    df = pl.read_parquet(result.persistence_path)
    assert df.shape[0] == 1
    assert df["view_date"][0] == datetime(2026, 1, 1, 0, 0)
    assert df["metric_value"][0] == approx(30.0)


def test_no_truncation_keeps_granular_dates(tmp_path: Path) -> None:
    aggregator = TimeAggregator(None)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]
    result = aggregator.run(_granular_view(rows, tmp_path), _metric(TimeOperator.SUM))
    df = pl.read_parquet(result.persistence_path).sort("view_date")
    assert df["view_date"].to_list() == [datetime(2026, 1, 1, 3, 0), datetime(2026, 1, 1, 20, 0)]
    assert df["metric_value"].to_list() == [approx(10.0), approx(20.0)]


def test_temporal_aggregation_avg(tmp_path: Path) -> None:
    aggregator = TimeAggregator(TimeAggregation.DAY)
    rows = [(datetime(2026, 1, 1, 1, 0), 10.0), (datetime(2026, 1, 1, 2, 0), 20.0)]

    with pytest.raises(NotImplementedError):
        aggregator.run(_granular_view(rows, tmp_path), _metric(TimeOperator.AVG))


def test_part_counter_increments_file_names(tmp_path: Path) -> None:
    aggregator = TimeAggregator(TimeAggregation.DAY)
    metric = _metric(TimeOperator.SUM)
    rows = [(datetime(2026, 1, 1, 3, 0), 10.0), (datetime(2026, 1, 1, 20, 0), 20.0)]

    first = aggregator.run(_granular_view(rows, tmp_path), metric)
    second = aggregator.run(_granular_view(rows, tmp_path), metric)

    assert first.persistence_path != second.persistence_path
    assert first.persistence_path.name.endswith("-0.parquet")
    assert second.persistence_path.name.endswith("-1.parquet")

    # Each part is truncated to its day and the two intra-day values are summed.
    for part in (first, second):
        df = pl.read_parquet(part.persistence_path)
        assert df.shape[0] == 1
        assert df["view_date"][0] == datetime(2026, 1, 1, 0, 0)
        assert df["metric_value"][0] == approx(30.0)
