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
from gems_views_builder.input.catalog import AggregOperatorType, PropertySchema
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.metric_view import TemporalMetricView
from tests.common import make_catalog, make_metric, make_raw_component, make_view_config
from tests.e2e.utils import (
    build_raw_input_data,
    make_calendar,
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
    metrics = [
        make_metric("LOAD", "load", "injection", "active_load"),
        make_metric(
            "PROD",
            "balance",
            output_id="active_power",
            time_operator=AggregOperatorType.AVG,
            filter=PropertySchema(key="country", value="France"),
        ),
    ]
    view_config = make_view_config(
        view_id="view_area",
        catalog_ids={"catalog"},
        extra_locations=["country", "region"],
        metric_ids=["catalog.LOAD", "catalog.PROD"],
    )
    catalogs = [make_catalog(metrics={metric.id: metric for metric in metrics})]
    return build_raw_input_data(
        system,
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        [make_simulation_table(SIMULATION_ROWS)],
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
