# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import polars as pl
from pytest import approx

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.metric_structure_table import MetricStructureTable


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
    rows: list[dict[str, object]] = [
        {
            "metric_id": "M",
            "component": "comp",
            "metric_location": "L",
            "breakdown_properties": "",
            "output": "out",
            "weight_output_id": "1",
        }
    ]
    return MetricStructureTable(rows, "M")


def _metric(terms_operator: AggregOperatorType) -> Metric:
    return Metric(id="M", terms=[], terms_operator=terms_operator, time_operator=AggregOperatorType.SUM)


def test_terms_aggregation_sum(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(AggregOperatorType.SUM))
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(5.0)


def test_terms_aggregation_avg(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(AggregOperatorType.AVG))
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(2.5)
