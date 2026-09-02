# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import polars as pl
from pytest import approx

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.simulation_table import FilteredSimulationTable, join
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.metric_view import persist_metric_view


def create_filtered_st(values: list[float], tmp_path: Path) -> FilteredSimulationTable:
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


def create_metric_structure_table() -> MetricStructureTable:
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


def test_terms_aggregation_sum(tmp_path: Path) -> None:
    # Arrange
    filtered_st = create_filtered_st([2.0, 3.0], tmp_path)
    metric_structure_table = create_metric_structure_table()
    aggregator = TermsAggregator()

    # Act
    structured_simulation_table = persist_metric_view(join(metric_structure_table, filtered_st))
    metric_view = aggregator.run(
        structured_simulation_table,
        Metric(id="M", terms=[], terms_operator=AggregOperatorType.SUM, time_operator=AggregOperatorType.SUM),
    )

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(5.0)


def test_terms_aggregation_avg(tmp_path: Path) -> None:
    # Arrange
    filtered_st = create_filtered_st([2.0, 3.0], tmp_path)
    metric_structure_table = create_metric_structure_table()
    aggregator = TermsAggregator()

    # Act
    structured_simulation_table = persist_metric_view(join(metric_structure_table, filtered_st))
    metric_view = aggregator.run(
        structured_simulation_table,
        Metric(id="M", terms=[], terms_operator=AggregOperatorType.AVG, time_operator=AggregOperatorType.SUM),
    )

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(2.5)
