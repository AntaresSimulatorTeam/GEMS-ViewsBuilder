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

from gems_views_builder.common import METRIC_STRUCTURE_TABLE_SCHEMA
from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.terms_aggregator import TermsAggregator


def _filtered_st(values: list[float], tmp_path: Path) -> FilteredSimulationTable:
    """Filtered simulation rows for a single component/output at one timestep and scenario."""
    n = len(values)
    dataframe = pl.DataFrame(
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
    return FilteredSimulationTable(tmp_path / "dummy.parquet", dataframe)


def _structure() -> MetricStructureTable:
    """Metric structure mapping comp/out to metric M at location L."""
    rows = pl.DataFrame(
        {
            "metric_id": ["M"],
            "component": ["comp"],
            "metric_location": ["L"],
            "breakdown_properties": [""],
            "output": ["out"],
            "weight_output_id": ["1"],
        },
        schema=METRIC_STRUCTURE_TABLE_SCHEMA,
    )
    return MetricStructureTable(rows, "M")


def _metric(terms_operator: TermsOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=terms_operator, time_operator=TimeOperator.SUM)


def test_terms_aggregation_sum(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(TermsOperator.SUM))
    df = pl.read_parquet(metric_view.file_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(5.0)


def test_terms_aggregation_avg(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(TermsOperator.AVG))
    df = pl.read_parquet(metric_view.file_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(2.5)
