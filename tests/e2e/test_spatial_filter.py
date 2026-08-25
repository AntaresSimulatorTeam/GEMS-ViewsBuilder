# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl

from gems_views_builder.__main__ import build_metric_views
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.view import ParquetViewSinker, accumulate_on_disk
from tests.e2e.utils import (
    build_raw_input_data,
    create_results_dir,
    make_raw_component,
    make_raw_connection,
    make_simulation_table_and_calendar,
)

TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}

T1 = datetime(2026, 1, 1, 3, 0)
T2 = datetime(2026, 1, 1, 20, 0)

ALL_PROD_LOCATIONS = {"busA", "busB", "busC", "France", "Germany", "West", "East"}


def make_system() -> Any:
    return SimpleNamespace(
        components=[
            make_raw_component("busA", "lib.bus", {"country": "France", "region": "West"}),
            make_raw_component("busB", "lib.bus", {"country": "France", "region": "East"}),
            make_raw_component("busC", "lib.bus", {"country": "Germany"}),
            make_raw_component("loadX", "lib.load", {}),
        ],
        connections=[make_raw_connection("loadX", "injection", "busA", "injection")],
    )


def make_metrics() -> list[Metric]:
    return [
        Metric(
            id="PROD",
            terms=[Term(taxonomy_category="balance", output_id="active_power", location_port=None)],
            terms_operator=AggregOperatorType.SUM,
            time_operator=AggregOperatorType.AVG,
        )
    ]


def make_view_config(spatial_filter: list[str] | None) -> ViewConfig:
    return ViewConfig(
        id="view_area",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        catalog_ids={"catalog"},
        aggregation_patterns=(
            AggregationPattern(
                id="hourly",
                time_granularity=TimeGranularity.HOUR,
                scenario=False,
                spatial_filter=spatial_filter,
            ),
        ),
        extra_locations=["country", "region"],
        metric_ids=["catalog.PROD"],
    )


def make_catalogs(metrics: list[Metric]) -> dict[str, Catalog]:
    return {
        "catalog": Catalog(
            id="catalog",
            taxonomy="taxonomy",
            location_taxonomy_category="balance",
            metrics={"PROD": metrics[0]},
        )
    }


def build_input(tmp_path: Path, spatial_filter: list[str] | None) -> RawInputData:
    metrics = make_metrics()
    simulation_table, calendar = make_simulation_table_and_calendar(
        [
            ("busA", "active_power", 0, T1, 100.0),
            ("busA", "active_power", 0, T2, 200.0),
            ("busB", "active_power", 0, T1, 50.0),
            ("busB", "active_power", 0, T2, 150.0),
            ("busC", "active_power", 0, T1, 999.0),
            ("busC", "active_power", 0, T2, 999.0),
        ],
        tmp_path,
    )
    return build_raw_input_data(
        make_system(),
        TAXONOMY_CATEGORY_BY_MODEL,
        make_view_config(spatial_filter),
        simulation_table,
        calendar,
        catalogs=make_catalogs(metrics),
    )


def prod_locations(results_dir: Path) -> set[str]:
    # # All scenarios with same time granularity are written into same time granularity file
    view_path = next(results_dir.glob("view_hour_*.parquet"))
    return set(pl.read_parquet(view_path)["metric_location"].unique().to_list())


def test_spatial_filter_keeps_only_listed_locations(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path, spatial_filter=["busA"])
    results_dir = create_results_dir(tmp_path)

    # Act
    accumulate_on_disk(build_metric_views(input_data), ParquetViewSinker(results_dir))

    # Assert
    assert prod_locations(results_dir) == {"busA"}


def test_spatial_filter_none_keeps_all_locations(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path, spatial_filter=None)
    results_dir = create_results_dir(tmp_path)

    # Act
    accumulate_on_disk(build_metric_views(input_data), ParquetViewSinker(results_dir))

    # Assert
    assert prod_locations(results_dir) == ALL_PROD_LOCATIONS
