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

from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
from gems_views_builder.metric_view import MetricView
from gems_views_builder.time_aggregator import TimeAggregator


def _granular_view(values: list[float], tmp_path: Path) -> MetricView:
    """Granular metric-view parquet (output of the terms aggregation step)."""
    n = len(values)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": ["L"] * n,
            "breakdown_properties": [""] * n,
            "absolute_time_index": list(range(1, n + 1)),
            "scenario": [0] * n,
            "granular_metric_value": values,
            "granular_date": ["2026-01-01"] * n,
        }
    )
    path = tmp_path / "granular.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def _metric(time_operator: TimeOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=TermsOperator.SUM, time_operator=time_operator)


def test_temporal_aggregation_sum(tmp_path: Path) -> None:
    aggregator = TimeAggregator()
    result = aggregator.run(_granular_view([10.0, 20.0], tmp_path), _metric(TimeOperator.SUM))
    df = pl.read_parquet(result.file_path)
    assert df.shape[0] == 1
    assert df["metric_value"][0] == pytest.approx(30.0)


def test_temporal_aggregation_avg(tmp_path: Path) -> None:
    aggregator = TimeAggregator()
    with pytest.raises(NotImplementedError):
        aggregator.run(_granular_view([10.0, 20.0], tmp_path), _metric(TimeOperator.AVG))


def test_part_counter_increments_file_names(tmp_path: Path) -> None:
    aggregator = TimeAggregator()
    metric = _metric(TimeOperator.SUM)

    first = aggregator.run(_granular_view([1.0], tmp_path), metric)
    second = aggregator.run(_granular_view([1.0], tmp_path), metric)

    assert first.file_path != second.file_path
    assert first.file_path.name.endswith("-0.parquet")
    assert second.file_path.name.endswith("-1.parquet")
