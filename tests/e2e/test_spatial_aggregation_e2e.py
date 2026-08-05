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
from typing import Any

import polars as pl
from pytest import approx

from gems_views_builder.__main__ import build_metric_views
from gems_views_builder.input.catalog import Metric, PropertySchema, Term, TermsOperator, TimeOperator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.view.view import accumulate_on_disk
from gems_views_builder.view.view_sinker import ParquetViewSinker
from tests.e2e.utils import (
    build_input_data,
    make_filtered_simulation_table,
    make_raw_component,
    make_raw_connection,
)

EXTRA_LOCATIONS = ["country", "region"]
TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}

T1 = datetime(2026, 1, 1, 3, 0)
T2 = datetime(2026, 1, 1, 20, 0)


def build_input(tmp_path: Path) -> InputData:
    raw_components: list[Any] = [
        make_raw_component("busA", "lib.bus", {"country": "France", "region": "West"}),
        make_raw_component("busB", "lib.bus", {"country": "France", "region": "East"}),
        make_raw_component("busC", "lib.bus", {"country": "Germany"}),
        make_raw_component("loadX", "lib.load", {}),
    ]
    raw_connections: list[Any] = [make_raw_connection("loadX", "injection", "busA", "injection")]

    load_metric = Metric(
        id="LOAD",
        terms=[Term(taxonomy_category="load", output_id="active_load", location_port="injection")],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    prod_metric = Metric(
        id="PROD",
        terms=[Term(taxonomy_category="balance", output_id="active_power", location_port=None)],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.AVG,
        filter=PropertySchema(key="country", value="France"),
    )

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

    view_config = ViewConfig(
        id="view_area",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category="balance",
        catalog_ids=set(),  # keeps validate_catalogs_against_taxonomy disk-free (no catalogs to load)
        time_aggregation=None,
        extra_locations=EXTRA_LOCATIONS,
        metric_ids=["catalog.LOAD", "catalog.PROD"],
        metrics=[load_metric, prod_metric],
    )
    return build_input_data(
        tmp_path,
        raw_components,
        raw_connections,
        TAXONOMY_CATEGORY_BY_MODEL,
        view_config,
        make_filtered_simulation_table(rows, tmp_path),
    )


def values_by_location_and_date(path: Path) -> dict[tuple[str, datetime], float]:
    df = pl.read_parquet(path)
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


def test_all_view_config_locations_are_present(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)

    # Act
    metric_views = build_metric_views(input_data)

    # Assert
    load_view, prod_view = metric_views
    load_values = values_by_location_and_date(load_view.persistence_path)
    assert set(load_values) == set(EXPECTED_LOAD)
    for key, expected_value in EXPECTED_LOAD.items():
        assert load_values[key] == approx(expected_value)

    prod_values = values_by_location_and_date(prod_view.persistence_path)
    assert set(prod_values) == set(EXPECTED_PROD)
    assert all(location != "busC" for location, _ in prod_values)
    assert all(location != "Germany" for location, _ in prod_values)
    for key, expected_value in EXPECTED_PROD.items():
        assert prod_values[key] == approx(expected_value)

    assert input_data.view_config.extra_locations == EXTRA_LOCATIONS


def test_temporal_views_are_consistent_with_each_other(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)

    # Act
    metric_views = build_metric_views(input_data)

    # Assert
    load_view, prod_view = metric_views
    load_df = pl.read_parquet(load_view.persistence_path)
    prod_df = pl.read_parquet(prod_view.persistence_path)

    assert set(load_df["view_date"].to_list()) == {T1, T2}
    assert set(prod_df["view_date"].to_list()) == {T1, T2}
    assert set(load_df["breakdown_properties"].to_list()) == {"{}"}
    assert set(prod_df["breakdown_properties"].to_list()) == {"{}"}

    shared_locations = {"busA", "France", "West"}
    assert shared_locations <= set(load_df["metric_location"].to_list())
    assert shared_locations <= set(prod_df["metric_location"].to_list())

    assert set(load_df["metric_id"].to_list()) == {"LOAD"}
    assert set(prod_df["metric_id"].to_list()) == {"PROD"}


def test_merged_view_is_consistent_with_pre_merge_temporal_views(tmp_path: Path) -> None:
    # Arrange
    input_data = build_input(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Act
    metric_views = build_metric_views(input_data)
    accumulate_on_disk(metric_views, ParquetViewSinker(results_dir))
    merged = pl.read_parquet(next(results_dir.glob("view*.parquet")))

    # Assert
    pre_merge_row_counts = [pl.read_parquet(v.persistence_path).shape[0] for v in metric_views]
    assert merged.shape[0] == sum(pre_merge_row_counts)
    assert merged.filter(pl.col("metric_id") == "LOAD").shape[0] == len(EXPECTED_LOAD)
    assert merged.filter(pl.col("metric_id") == "PROD").shape[0] == len(EXPECTED_PROD)

    for metric_id, expected in (("LOAD", EXPECTED_LOAD), ("PROD", EXPECTED_PROD)):
        rows = merged.filter(pl.col("metric_id") == metric_id)
        by_key = dict(
            zip(
                zip(rows["metric_location"].to_list(), rows["view_date"].to_list()),
                rows["metric_value"].to_list(),
            )
        )
        assert set(by_key) == set(expected)
        for key, expected_value in expected.items():
            assert by_key[key] == approx(expected_value)

    prod_rows = merged.filter(pl.col("metric_id") == "PROD")
    assert "busC" not in prod_rows["metric_location"].to_list()
    assert "Germany" not in prod_rows["metric_location"].to_list()
