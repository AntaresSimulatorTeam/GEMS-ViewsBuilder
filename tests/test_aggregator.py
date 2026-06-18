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
from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.metrics_builder import MetricStructure


def _simu_lf(values: list[float]) -> pl.LazyFrame:
    """Minimal simulation-table lazy frame with the columns needed after the join."""
    n = len(values)
    return pl.DataFrame(
        {
            "component": ["comp"] * n,
            "output": ["out"] * n,
            "absolute_time_index": [1] * n,
            "block_time_index": [1] * n,
            "scenario_index": [0] * n,
            "value": values,
            "granular_date": ["2026-01-01"] * n,
            "block": ["B"] * n,
            "basis_status": ["B"] * n,
        }
    ).lazy()


def _structure_lf() -> pl.LazyFrame:
    """Minimal metric-structure lazy frame."""
    return pl.DataFrame(
        {
            "metric_id": ["M"],
            "component": ["comp"],
            "metric_location": ["L"],
            "breakdown_properties": [""],
            "output": ["out"],
            "weight_output_id": [1],
        }
    ).lazy()


def _metric(terms_op: TermsOperator, time_op: TimeOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=terms_op, time_operator=time_op)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_aggregate_terms_sum(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    mv = agg.aggregate(
        FilteredSimulationTable(tmp_path / "dummy", _simu_lf([2.0, 3.0])),
        MetricStructure(tmp_path / "dummy", _structure_lf()),
        _metric(TermsOperator.SUM, TimeOperator.SUM),
    )
    df = pl.read_parquet(mv.file)
    assert df.shape[0] == 1
    assert df["metric_value"][0] == approx(5.0)


def test_aggregate_terms_avg(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    mv = agg.aggregate(
        FilteredSimulationTable(tmp_path / "dummy", _simu_lf([2.0, 3.0])),
        MetricStructure(tmp_path / "dummy", _structure_lf()),
        _metric(TermsOperator.AVG, TimeOperator.SUM),
    )
    df = pl.read_parquet(mv.file)
    assert df.shape[0] == 1
    assert df["metric_value"][0] == approx(2.5)


def test_aggregate_part_counter_increments(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    metric = _metric(TermsOperator.SUM, TimeOperator.SUM)
    simu = FilteredSimulationTable(tmp_path / "dummy", _simu_lf([1.0]))
    struct = MetricStructure(tmp_path / "dummy", _structure_lf())

    mv0 = agg.aggregate(simu, struct, metric)
    mv1 = agg.aggregate(simu, struct, metric)

    assert mv0.file != mv1.file
    assert mv0.file.name.endswith("-0.parquet")
    assert mv1.file.name.endswith("-1.parquet")
