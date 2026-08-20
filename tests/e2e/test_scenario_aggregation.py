# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""
E2E test for scenario aggregation through the view-building process.

PatternRunner emits one temporal view per (time, scenario, scenario_id).
accumulate_on_disk then writes one result file per time granularity, merging
every pattern that shares that time.
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl

from gems_views_builder.__main__ import run_view_building_process
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import Pattern, TimeGranularity, ViewConfig
from gems_views_builder.view import ParquetViewSinker
from tests.e2e.utils import (
    build_raw_input_data,
    make_raw_component,
    make_raw_connection,
    make_results_dir,
    make_simulation_table_and_calendar,
)

TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}

T1 = datetime(2026, 1, 1, 3, 0)
T2 = datetime(2026, 1, 1, 20, 0)

PATTERNS = (
    Pattern(id="hourly", time=TimeGranularity.HOUR, scenario=False),
    Pattern(id="hourly2", time=TimeGranularity.HOUR, scenario=True),
    Pattern(id="daily", time=TimeGranularity.DAY, scenario=False),
    Pattern(id="daily2", time=TimeGranularity.DAY, scenario=True),
    Pattern(id="monthly", time=TimeGranularity.MONTH, scenario=False),
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


def make_view_config(tmp_path: Path) -> ViewConfig:
    return ViewConfig(
        id="view_area",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category="balance",
        catalog_ids={"catalog"},
        patterns=PATTERNS,
        metric_ids={"catalog.LOAD", "catalog.PROD"},
    )


def make_catalogs(metrics: list[Metric]) -> dict[str, Catalog]:
    load_metric, prod_metric = metrics
    return {
        "catalog": Catalog(
            id="catalog",
            taxonomy="taxonomy",
            location_taxonomy_category="balance",
            metrics={"LOAD": load_metric, "PROD": prod_metric},
        )
    }


def build_input(tmp_path: Path) -> RawInputData:
    system = make_system()
    metrics = make_metrics()
    view_config = make_view_config(tmp_path)
    catalogs = make_catalogs(metrics)
    simulation_table, calendar = make_simulation_table_and_calendar(
        [
            ("loadX", "active_load", 0, T1, 10.0),
            ("loadX", "active_load", 0, T2, 20.0),
            ("busA", "active_power", 0, T1, 100.0),
            ("busA", "active_power", 0, T2, 200.0),
        ],
        tmp_path,
    )
    return build_raw_input_data(
        tmp_path,
        system,
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        simulation_table,
        calendar,
        catalogs=catalogs,
    )


def result_files_by_time_granularity(results_dir: Path) -> dict[str, Path]:
    # Output files are named view_{time}_{timestamp}.parquet
    return {path.stem.split("_")[1]: path for path in results_dir.glob("view_*.parquet")}


def test_one_output_file_per_time_granularity_merges_all_scenarios(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)
    results_dir = make_results_dir(tmp_path)

    # Act
    run_view_building_process(input_data, ParquetViewSinker(results_dir))

    result_files = result_files_by_time_granularity(results_dir)
    hour_view = pl.read_parquet(result_files["hour"])
    day_view = pl.read_parquet(result_files["day"])

    # Assert
    assert set(result_files) == {"hour", "day", "month"}
    assert len(result_files) == 3
    assert set(hour_view["metric_id"].to_list()) == {"LOAD", "PROD"}
    assert set(hour_view["scenario_aggregation"].to_list()) == {True, False}
    assert set(day_view["metric_id"].to_list()) == {"LOAD", "PROD"}
    assert set(day_view["scenario_aggregation"].to_list()) == {True, False}
