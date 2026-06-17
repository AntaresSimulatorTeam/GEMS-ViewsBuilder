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
from pytest import approx

from gems_views_builder.aggregator import Aggregator
from gems_views_builder.input.catalog import TermsOperator, TimeOperator


def _joined_df(values: list[float]) -> pl.LazyFrame:
    """
    Minimal columns required by Aggregator.aggregate_metric_terms().
    """
    return pl.DataFrame(
        {
            "metric_id": ["M"] * len(values),
            "metric_location": ["L"] * len(values),
            "breakdown_properties": [""] * len(values),
            "absolute_time_index": [1] * len(values),
            "scenario_index": [0] * len(values),
            "value": values,
            # at least one non-null per group, strings are fine for grouping here
            "granular_date": ["2026-01-01"] * len(values),
        }
    ).lazy()


def test_aggregate_metric_terms_sum(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    out_path = agg.aggregate_metric_terms(_joined_df([2.0, 3.0]), TermsOperator.SUM, metric_id="M")

    df = pl.read_parquet(out_path)
    assert df.shape[0] == 1
    assert approx(df["granular_metric_value"][0]) == 5.0


def test_aggregate_metric_terms_avg(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    out_path = agg.aggregate_metric_terms(_joined_df([2.0, 3.0]), TermsOperator.AVG, metric_id="M")

    df = pl.read_parquet(out_path)
    assert df.shape[0] == 1
    assert approx(df["granular_metric_value"][0]) == 2.5


def test_aggregate_metric_temporally_sum_and_part_counter(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)

    metric_view_path = agg.aggregate_metric_terms(_joined_df([1.0, 2.0]), TermsOperator.SUM, metric_id="M")

    part0 = agg.aggregate_metric_temporally(metric_view_path, TimeOperator.SUM, metric_id="M")
    df0 = pl.read_parquet(part0)
    assert df0.shape[0] == 1
    assert approx(df0["metric_value"][0]) == 3.0

    part1 = agg.aggregate_metric_temporally(metric_view_path, TimeOperator.SUM, metric_id="M")
    assert part1 != part0
    assert part0.name.endswith("-0.parquet")
    assert part1.name.endswith("-1.parquet")
