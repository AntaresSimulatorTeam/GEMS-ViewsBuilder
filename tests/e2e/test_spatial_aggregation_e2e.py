# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""E2E test for spatial aggregation.

Everything (raw system components/connections, library, taxonomy, view config, simulation
table) is built in code -- no YAML/parquet fixture files are used. The one pipeline step that
*is* skipped is ``Loader(input_dir).load()`` (disk I/O); every other step of
``run_view_building_process`` runs for real, via ``pipeline_helpers.run_pipeline``:
``create_components`` -> ``supply_components_with_taxonomy_categories`` ->
``build_component_port_connections`` -> ``supply_components_with_port_connections`` ->
``group_components_by_taxon`` -> ``supply_components_with_locations`` ->
``MetricStructureTableBuilder`` -> ``validate_catalogs_against_taxonomy`` -> ``ViewBuilder``
(``TermsAggregator`` -> ``TimeAggregator``), then merged (``accumulate_on_disk``), to check:

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

from gems_views_builder.input.catalog import Metric, PropertySchema, Term, TermsOperator, TimeOperator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.view_config import TimeAggregation, ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.view.view import View, accumulate_on_disk
from gems_views_builder.view.view_sinker import ParquetViewSinker
from tests.e2e.utils import build_input_data, make_raw_component, make_raw_connection, run_pipeline

EXTRA_LOCATIONS = ["country", "region"]
TAXONOMY_CATEGORY_BY_MODEL = {"bus": "balance", "load": "load"}


def make_filtered_simulation_table(
    rows: list[tuple[str, str, int, datetime, float]], tmp_path: Path
) -> FilteredSimulationTable:
    n = len(rows)
    dataframe = pl.DataFrame(
        {
            "block": ["b1"] * n,
            "component": [r[0] for r in rows],
            "output": [r[1] for r in rows],
            "absolute_time_index": list(range(1, n + 1)),
            "block_time_index": list(range(1, n + 1)),
            "scenario_index": [r[2] for r in rows],
            "value": [r[4] for r in rows],
            "basis_status": ["ok"] * n,
            "granular_date": [r[3] for r in rows],
        },
        schema_overrides={"granular_date": pl.Datetime},
    )
    sim_table_dir = tmp_path / "filtered_simulation_table"
    sim_table_dir.mkdir()
    path = sim_table_dir / "filtered.parquet"
    dataframe.write_parquet(path)
    return FilteredSimulationTable(path, pl.scan_parquet(path))


def build_pipeline(tmp_path: Path) -> tuple[list[MetricView], ViewConfig]:
    # Component,Model,Properties
    raw_components: list[Any] = [
        make_raw_component("busA", "lib.bus", {"country": "France", "region": "West"}),
        make_raw_component("busB", "lib.bus", {"country": "France", "region": "East"}),
        make_raw_component("busC", "lib.bus", {"country": "Germany"}),
        make_raw_component("loadX", "lib.load", {}),
    ]

    # Connect loadX to busA through its injection port.
    raw_connections: list[Any] = [make_raw_connection("loadX", "injection", "busA", "injection")]

    load_metric = Metric(
        id="LOAD",
        terms=[Term(taxonomy_category="load", output_id="active_load", location_port="injection")],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    # PROD is scoped to France only, so busC (Germany) must be excluded from its output entirely.
    prod_metric = Metric(
        id="PROD",
        terms=[Term(taxonomy_category="balance", output_id="active_power", location_port=None)],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.AVG,
        filter=PropertySchema(key="country", value="France"),
    )
    metrics = [load_metric, prod_metric]

    # Two granular timesteps within the same day, per component/output.
    rows = [
        ("loadX", "active_load", 0, datetime(2026, 1, 1, 3, 0), 10.0),
        ("loadX", "active_load", 0, datetime(2026, 1, 1, 20, 0), 20.0),
        ("busA", "active_power", 0, datetime(2026, 1, 1, 3, 0), 100.0),
        ("busA", "active_power", 0, datetime(2026, 1, 1, 20, 0), 200.0),
        ("busB", "active_power", 0, datetime(2026, 1, 1, 3, 0), 50.0),
        ("busB", "active_power", 0, datetime(2026, 1, 1, 20, 0), 150.0),
        ("busC", "active_power", 0, datetime(2026, 1, 1, 3, 0), 999.0),  # filtering out by country=France
        ("busC", "active_power", 0, datetime(2026, 1, 1, 20, 0), 999.0),
    ]
    filtered_st = make_filtered_simulation_table(rows, tmp_path)

    view_config = ViewConfig(
        id="view_area",
        input_data_path=tmp_path,
        calendar_id="calendar",
        location_taxonomy_category="balance",
        catalog_ids=set(),  # keeps validate_catalogs_against_taxonomy disk-free (no catalogs to load)
        time_aggregation=TimeAggregation.DAY,
        extra_locations=EXTRA_LOCATIONS,
        metric_ids=["catalog.LOAD", "catalog.PROD"],
        metrics=metrics,
    )

    input_data: InputData = build_input_data(
        tmp_path, raw_components, raw_connections, TAXONOMY_CATEGORY_BY_MODEL, view_config, filtered_st
    )
    temporal_views = run_pipeline(input_data, tmp_path)
    return temporal_views, view_config


def values_by_location(path: Path) -> dict[str, float]:
    df = pl.read_parquet(path)
    return dict(zip(df["metric_location"].to_list(), df["metric_value"].to_list()))


# loadX's location is resolved through its port connection to busA, so LOAD is reported under
# busA's location (and busA's extra-locations), not under "loadX".

# Sum 10 + 20, loadX is connected to busA through its injection port busA==France==West location
# Load Metric has Time && Term Operator SUM, so the result is 30.0
EXPECTED_LOAD = {"busA": 30.0, "France": 30.0, "West": 30.0}

# Prod Metric has Time OP = Sum, Term OP = AVG
# Bus C won't appear because of filter
EXPECTED_PROD = {"busA": 150.0, "France": 125.0, "West": 150.0, "busB": 100.0, "East": 100.0}


def test_all_view_config_locations_are_present(tmp_path: Path) -> None:
    # Arrange / Act
    temporal_views, view_config = build_pipeline(tmp_path)
    load_view, prod_view = temporal_views

    # Assert: LOAD's location is port-resolved to busA, so busA's primary location plus every
    # extra-location property it actually has (view_config.extra_locations) must appear.
    load_locations = values_by_location(load_view.persistence_path)
    assert set(load_locations) == set(EXPECTED_LOAD)
    for location, expected_value in EXPECTED_LOAD.items():
        assert load_locations[location] == approx(expected_value)

    # PROD is filtered to country=France, so busC/Germany must be entirely absent
    # even though "country" is a configured extra location.
    prod_locations = values_by_location(prod_view.persistence_path)
    assert set(prod_locations) == set(EXPECTED_PROD)
    assert "busC" not in prod_locations
    assert "Germany" not in prod_locations
    for location, expected_value in EXPECTED_PROD.items():
        assert prod_locations[location] == approx(expected_value)

    assert view_config.extra_locations == EXTRA_LOCATIONS


def test_temporal_views_are_consistent_with_each_other(tmp_path: Path) -> None:
    # Arrange / Act
    temporal_views, _ = build_pipeline(tmp_path)
    load_view, prod_view = temporal_views
    load_df = pl.read_parquet(load_view.persistence_path)
    prod_df = pl.read_parquet(prod_view.persistence_path)

    # Assert: both metrics share the same time-aggregation config, so both must
    # collapse to a single view_date; neither metric has a breakdown, so both use "{}".
    assert set(load_df["view_date"].to_list()) == {datetime(2026, 1, 1)}
    assert set(prod_df["view_date"].to_list()) == {datetime(2026, 1, 1)}
    assert set(load_df["breakdown_properties"].to_list()) == {"{}"}
    assert set(prod_df["breakdown_properties"].to_list()) == {"{}"}

    # busA/France/West are shared between the two metrics (France is not filtered out of
    # either) and must be present in both views.
    shared_locations = {"busA", "France", "West"}
    assert shared_locations <= set(load_df["metric_location"].to_list())
    assert shared_locations <= set(prod_df["metric_location"].to_list())

    assert set(load_df["metric_id"].to_list()) == {"LOAD"}
    assert set(prod_df["metric_id"].to_list()) == {"PROD"}


def test_merged_view_is_consistent_with_pre_merge_temporal_views(tmp_path: Path) -> None:
    # Arrange
    temporal_views, _ = build_pipeline(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Act
    view: View = accumulate_on_disk(temporal_views, ParquetViewSinker(results_dir))
    merged = view.dataframe.collect()

    # Assert: row count and per-metric row counts must match the sum of the pre-merge views.
    pre_merge_row_counts = [pl.read_parquet(v.persistence_path).shape[0] for v in temporal_views]
    assert merged.shape[0] == sum(pre_merge_row_counts)
    assert merged.filter(pl.col("metric_id") == "LOAD").shape[0] == len(EXPECTED_LOAD)
    assert merged.filter(pl.col("metric_id") == "PROD").shape[0] == len(EXPECTED_PROD)

    # Assert: every value in the merged file matches the corresponding pre-merge temporal view.
    for metric_id, expected in (("LOAD", EXPECTED_LOAD), ("PROD", EXPECTED_PROD)):
        rows = merged.filter(pl.col("metric_id") == metric_id)
        by_location = dict(zip(rows["metric_location"].to_list(), rows["metric_value"].to_list()))
        assert set(by_location) == set(expected)
        for location, expected_value in expected.items():
            assert by_location[location] == approx(expected_value)

    # No location leaks across metrics in the merge: busC/Germany only ever came from PROD's
    # filter being applied; LOAD never touches them at all since loadX resolves to busA.
    prod_rows = merged.filter(pl.col("metric_id") == "PROD")
    assert "busC" not in prod_rows["metric_location"].to_list()
    assert "Germany" not in prod_rows["metric_location"].to_list()
