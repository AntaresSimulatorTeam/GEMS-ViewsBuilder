# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import polars as pl
import pytest
from pytest import approx

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import Metric, TermsOperator, TimeOperator
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


def _metric(terms_operator: TermsOperator) -> Metric:
    return Metric(id="M", terms=[], terms_operator=terms_operator, time_operator=TimeOperator.SUM)


def test_terms_aggregation_sum(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(TermsOperator.SUM))
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(5.0)


def test_terms_aggregation_avg(tmp_path: Path) -> None:
    aggregator = TermsAggregator(_filtered_st([2.0, 3.0], tmp_path))
    metric_view = aggregator.run(_structure(), _metric(TermsOperator.AVG))
    df = pl.read_parquet(metric_view.persistence_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == approx(2.5)


def _filtered_st_mixed_scenario_dependence(tmp_path: Path) -> FilteredSimulationTable:
    """Two outputs on the same component: 'var_cost' is scenario-dependent
    (10 @scenario 0, 20 @scenario 1) and 'fixed_cost' is scenario-independent
    (5, scenario_index=None), at a single timestep."""
    dataframe = pl.DataFrame(
        {
            "component": ["comp", "comp", "comp"],
            "output": ["var_cost", "var_cost", "fixed_cost"],
            "absolute_time_index": [1, 1, 1],
            "block_time_index": [1, 1, 1],
            "scenario_index": [0, 1, None],
            "value": [10.0, 20.0, 5.0],
            "granular_date": ["2026-01-01"] * 3,
            "block": ["B"] * 3,
            "basis_status": ["B"] * 3,
        }
    ).lazy()
    return FilteredSimulationTable(tmp_path / "dummy.parquet", dataframe)


def _structure_mixed_scenario_dependence() -> MetricStructureTable:
    """Metric M combines both outputs (terms) at the same location/breakdown."""
    rows: list[dict[str, object]] = [
        {
            "metric_id": "M",
            "component": "comp",
            "metric_location": "L",
            "breakdown_properties": "",
            "output": "var_cost",
            "weight_output_id": "1",
        },
        {
            "metric_id": "M",
            "component": "comp",
            "metric_location": "L",
            "breakdown_properties": "",
            "output": "fixed_cost",
            "weight_output_id": "1",
        },
    ]
    return MetricStructureTable(rows, "M")


@pytest.mark.xfail(
    reason=(
        "KNOWN BUG: TermsAggregator groups by scenario_id before combining a metric's "
        "terms, so a scenario-independent term (scenario_id=None) is aggregated separately "
        "from a scenario-dependent term instead of being broadcast into every scenario's "
        "total. Produces 3 rows (null->5, 0->10, 1->20) instead of 2 (0->15, 1->25)."
    ),
    strict=True,
)
def test_terms_aggregation_sum_mixed_scenario_dependence(tmp_path: Path) -> None:
    """A metric summing a scenario-dependent term (var_cost) and a scenario-independent
    term (fixed_cost) at the same location/breakdown should broadcast the
    scenario-independent value into every scenario's total: 0 -> 10+5=15, 1 -> 20+5=25."""
    aggregator = TermsAggregator(_filtered_st_mixed_scenario_dependence(tmp_path))
    metric_view = aggregator.run(_structure_mixed_scenario_dependence(), _metric(TermsOperator.SUM))
    df = pl.read_parquet(metric_view.persistence_path).sort("scenario_id")

    assert df.shape[0] == 2
    assert df["scenario_id"].to_list() == [0, 1]
    assert df["granular_metric_value"].to_list() == [approx(15.0), approx(25.0)]
