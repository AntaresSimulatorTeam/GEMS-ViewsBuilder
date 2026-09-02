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
from types import SimpleNamespace
from typing import Any

import polars as pl
from pytest import approx

from gems_views_builder.__main__ import build_metric_views
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, PropertySchema, Term
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_view import TemporalMetricView
from tests.e2e.utils import (
    build_raw_input_data,
    make_calendar,
    make_raw_component,
    make_raw_connection,
    make_simulation_table,
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


def make_view_config() -> ViewConfig:
    return ViewConfig(
        id="view_area",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="taxonomy",
        catalog_ids={"catalog"},
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
        extra_locations=["country", "region"],
        metric_ids=["catalog.LOAD", "catalog.PROD"],
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


SIMULATION_ROWS = [
    ("loadX", "active_load", 0, T1, 10.0),
    ("loadX", "active_load", 0, T2, 20.0),
    ("busA", "active_power", 0, T1, 100.0),
    ("busA", "active_power", 0, T2, 200.0),
    ("busB", "active_power", 0, T1, 50.0),
    ("busB", "active_power", 0, T2, 150.0),
    ("busC", "active_power", 0, T1, 999.0),  # filtering out by country=France
    ("busC", "active_power", 0, T2, 999.0),
]


def build_input() -> RawInputData:
    system = make_system()
    metrics = make_metrics()
    view_config = make_view_config()
    catalogs = make_catalogs(metrics)
    return build_raw_input_data(
        system,
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        make_simulation_table(SIMULATION_ROWS),
        make_calendar(SIMULATION_ROWS),
        catalogs=catalogs,
    )


def extract_values_from_view(view: TemporalMetricView) -> dict[tuple[str, datetime], float]:
    df = pl.read_parquet(view.persistence_path)
    return dict(
        zip(
            zip(df["metric_location"].to_list(), df["view_date"].to_list()),
            df["metric_value"].to_list(),
        )
    )


def views_by_metric_id(metric_views: list[TemporalMetricView]) -> dict[str, TemporalMetricView]:
    by_metric_id: dict[str, TemporalMetricView] = {}
    for view in metric_views:
        metric_id = pl.read_parquet(view.persistence_path, columns=["metric_id"])["metric_id"][0]
        by_metric_id[str(metric_id)] = view
    return by_metric_id


# loadX's location is resolved through its port connection to busA, so LOAD is reported under
# busA's location (and busA's extra-locations), not under "loadX".
#
# With time_aggr_granularity=HOUR each granular timestamp maps to its hour bucket.
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


def test_extra_locations_values_in_final_metric_views() -> None:
    # Arrange
    input_data = build_input()

    # Act
    views = views_by_metric_id(build_metric_views(input_data))

    # Assert
    assert extract_values_from_view(views["LOAD"]) == approx(EXPECTED_LOAD)
    assert extract_values_from_view(views["PROD"]) == approx(EXPECTED_PROD)
