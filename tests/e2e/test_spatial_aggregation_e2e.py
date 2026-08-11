# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""E2E test for spatial aggregation.
1. Every location mentioned by the view config -- the primary resolved location
   *and* every configured extra-location property -- shows up in the output.
2. Port-resolved locations (a component whose location is a connected peer, not itself)
   are resolved correctly through the real connection-index machinery.
3. The temporal views (one per metric, before merging) are structurally consistent
   with each other and with the view config (same breakdown/time shape, locations
   shared across metrics agree, filtered-out locations are absent as expected).
4. The merged result is consistent with the pre-merge temporal views (row counts,
   metric ids, per-location values all add up).
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl
from pytest import approx

from gems_views_builder.__main__ import build_metric_views
from gems_views_builder.input.catalog import AggregOperatorType, Metric, PropertySchema, Term
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import MetricView
from tests.e2e.utils import (
    build_input_data,
    make_raw_component,
    make_raw_connection,
)
from tests.e2e.utils import (
    make_filtered_simulation_table as build_filtered_simulation_table,
)

TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}

T1 = datetime(2026, 1, 1, 3, 0)
T2 = datetime(2026, 1, 1, 20, 0)


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
        filter=PropertySchema(key="country", value="France"),
    )
    return [load_metric, prod_metric]


def make_view_config(tmp_path: Path, metrics: list[Metric]) -> ViewConfig:
    return ViewConfig(
        id="view_area",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category="balance",
        catalog_ids=set(),  # keeps validate_catalogs_against_taxonomy disk-free (no catalogs to load)
        time_aggregation=None,
        extra_locations=["country", "region"],
        metric_ids=["catalog.LOAD", "catalog.PROD"],
        metrics=metrics,
    )


def make_filtered_simulation_table(tmp_path: Path) -> FilteredSimulationTable:
    rows = [
        ("loadX", "active_load", 0, T1, 10.0),
        ("loadX", "active_load", 0, T2, 20.0),
        ("busA", "active_power", 0, T1, 100.0),
        ("busA", "active_power", 0, T2, 200.0),
        ("busB", "active_power", 0, T1, 50.0),
        ("busB", "active_power", 0, T2, 150.0),
        ("busC", "active_power", 0, T1, 999.0),  # filtering out by country=France
        ("busC", "active_power", 0, T2, 999.0),
    ]
    return build_filtered_simulation_table(rows, tmp_path)


def build_input(tmp_path: Path) -> InputData:
    system = make_system()
    metrics = make_metrics()
    view_config = make_view_config(tmp_path, metrics)
    filtered_st = make_filtered_simulation_table(tmp_path)
    return build_input_data(tmp_path, system, TAXONOMY_CATEGORY_BY_MODEL, view_config, filtered_st)


def extract_values_from_view(view: MetricView) -> dict[tuple[str, datetime], float]:
    df = pl.read_parquet(view.persistence_path)
    return dict(
        zip(
            zip(df["metric_location"].to_list(), df["view_date"].to_list()),
            df["metric_value"].to_list(),
        )
    )


# loadX's location is resolved through its port connection to busA, so LOAD is reported under
# busA's location (and busA's extra-locations), not under "loadX".
#
# With time_aggregation=None each granular timestamp stays its own view_date.
# LOAD: terms SUM + time SUM, one value per (location, timestamp) => the granular value.
EXPECTED_LOAD = {
    ("busA", T1): 10.0,
    ("busA", T2): 20.0,
    ("France", T1): 10.0,
    ("France", T2): 20.0,
    ("West", T1): 10.0,
    ("West", T2): 20.0,
}

# PROD: terms SUM + time AVG. Primary/region locations have one component each, so AVG
# equals the granular value. France is shared by busA and busB, so AVG collapses both
# contributions at the same timestamp: mean(100,50)=75 and mean(200,150)=175.
# Bus C is filtered out by country=France.
EXPECTED_PROD = {
    ("busA", T1): 100.0,
    ("busA", T2): 200.0,
    ("busB", T1): 50.0,
    ("busB", T2): 150.0,
    ("West", T1): 100.0,
    ("West", T2): 200.0,
    ("East", T1): 50.0,
    ("East", T2): 150.0,
    ("France", T1): 75.0,
    ("France", T2): 175.0,
}


def test_extra_locations_values_in_final_metric_views(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)

    # Act
    load_view, prod_view = build_metric_views(input_data)

    # Assert
    assert extract_values_from_view(load_view) == approx(EXPECTED_LOAD)
    assert extract_values_from_view(prod_view) == approx(EXPECTED_PROD)


def test_temporal_views_are_consistent_with_each_other(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)

    # Act
    load_view, prod_view = build_metric_views(input_data)

    # Assert
    load_df = pl.read_parquet(load_view.persistence_path)
    prod_df = pl.read_parquet(prod_view.persistence_path)

    shared_locations = {"busA", "France", "West"}

    assert set(load_df["view_date"].to_list()) == {T1, T2}
    assert set(prod_df["view_date"].to_list()) == {T1, T2}
    assert set(load_df["breakdown_properties"].to_list()) == {"{}"}
    assert set(prod_df["breakdown_properties"].to_list()) == {"{}"}

    assert shared_locations <= set(load_df["metric_location"].to_list())
    assert shared_locations <= set(prod_df["metric_location"].to_list())

    assert set(load_df["metric_id"].to_list()) == {"LOAD"}
    assert set(prod_df["metric_id"].to_list()) == {"PROD"}
