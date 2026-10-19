# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""
E2E test for scenario aggregation through the view-building process.

Each aggregation pattern produces its own result file, named
{view_config_id}_{aggregation_pattern_id}_{time_granularity}_{scenario}_{timestamp}.parquet.
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl

from gems_views_builder.__main__ import build_components_by_taxon, build_metric_views
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_building_input_data import create_view_building_inputs
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.view import ParquetViewSinker, accumulate_on_disk
from tests.e2e.utils import (
    build_raw_input_data,
    create_results_dir,
    make_calendar,
    make_raw_component,
    make_raw_connection,
    make_simulation_table,
)

TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}

T1 = datetime(2026, 1, 1, 3, 0)
T2 = datetime(2026, 1, 1, 20, 0)

PATTERNS = (
    AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),
    AggregationPattern(id="hourly2", time_granularity=TimeGranularity.HOUR, scenario=True),
    AggregationPattern(id="daily", time_granularity=TimeGranularity.DAY, scenario=False),
    AggregationPattern(id="daily2", time_granularity=TimeGranularity.DAY, scenario=True),
    AggregationPattern(id="monthly", time_granularity=TimeGranularity.MONTH, scenario=False),
)


def make_system() -> Any:
    return SimpleNamespace(
        components=[
            make_raw_component("busA", "lib.bus", {"country": "France"}),
            make_raw_component("loadX", "lib.load", {}),
        ],
        connections=[make_raw_connection("loadX", "injection", "busA", "injection")],
    )


def make_metrics() -> list[Metric]:
    load_metric = Metric(
        id="LOAD",
        terms=[Term(taxonomy_category="load", output_id="active_load", location_port="injection")],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
    )
    prod_metric = Metric(
        id="PROD",
        terms=[Term(taxonomy_category="balance", output_id="active_power", location_port=None)],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.AVG,
    )
    return [load_metric, prod_metric]


def make_view_config() -> ViewConfig:
    return ViewConfig(
        id="view_area",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="taxonomy",
        aggregation_patterns=PATTERNS,
        full_metric_ids=["catalog.LOAD", "catalog.PROD"],
    )


def make_catalogs(metrics: list[Metric]) -> list[Catalog]:
    load_metric, prod_metric = metrics
    return [
        Catalog(
            id="catalog",
            taxonomy="taxonomy",
            location_taxonomy_category="balance",
            metrics={"LOAD": load_metric, "PROD": prod_metric},
        )
    ]


def build_input() -> RawInputData:
    system = make_system()
    metrics = make_metrics()
    view_config = make_view_config()
    catalogs = make_catalogs(metrics)
    rows = [
        ("loadX", "active_load", 0, T1, 10.0),
        ("loadX", "active_load", 0, T2, 20.0),
        ("busA", "active_power", 0, T1, 100.0),
        ("busA", "active_power", 0, T2, 200.0),
    ]
    return build_raw_input_data(
        system,
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        [make_simulation_table(rows)],
        make_calendar(rows),
        catalogs=catalogs,
    )


def fetch_result_files(results_dir: Path) -> list[Path]:
    return list(results_dir.glob("*.parquet"))


def result_name(path: Path) -> str:
    # Timestamp is appended as a final _{timestamp} segment with no underscore inside it.
    return path.stem.rsplit("_", 1)[0]


def test_one_output_file_per_aggregation_pattern(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input()
    results_dir = create_results_dir(tmp_path)
    components_by_taxon = build_components_by_taxon(input_data)
    sinker = ParquetViewSinker(results_dir)

    # Act
    for view_building_input in create_view_building_inputs(input_data):
        metric_views = build_metric_views(view_building_input, components_by_taxon)
        accumulate_on_disk(metric_views, sinker)
        del metric_views

    # Assert
    result = {result_name(path): path for path in fetch_result_files(results_dir)}
    hourly = pl.read_parquet(result["view_area_hourly_hour_false"])
    hourly_aggregated = pl.read_parquet(result["view_area_hourly2_hour_true"])
    daily = pl.read_parquet(result["view_area_daily_day_false"])
    daily_aggregated = pl.read_parquet(result["view_area_daily2_day_true"])

    assert set(result) == {
        "view_area_hourly_hour_false",
        "view_area_hourly2_hour_true",
        "view_area_daily_day_false",
        "view_area_daily2_day_true",
        "view_area_monthly_month_false",
    }
    assert set(hourly["metric_id"].to_list()) == {"LOAD", "PROD"}
    assert set(hourly["scenario_aggregation"].to_list()) == {False}
    assert set(hourly_aggregated["scenario_aggregation"].to_list()) == {True}
    assert set(daily["metric_id"].to_list()) == {"LOAD", "PROD"}
    assert set(daily["scenario_aggregation"].to_list()) == {False}
    assert set(daily_aggregated["scenario_aggregation"].to_list()) == {True}
