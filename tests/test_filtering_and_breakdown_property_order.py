# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Regression tests: component property declaration order must not affect breakdown groupby."""

from __future__ import annotations

import shutil
from numbers import Real
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder import (
    MetricStructureTableBuilder,
    load_catalog,
    load_library,
)
from gems_views_builder.__main__ import run_view_building_process
from gems_views_builder.input.component import (
    Component,
    build_component_port_connections,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.view import ParquetViewSinker
from tests.conftest import paths_from_dataset

# Same (technology, company) as filtering_and_breakdown, but YAML property order differs per component.
_GAS_RHONEPOWER_GENERATORS = ("gas_1", "gas_2")
_GAS_RHONEPOWER_BREAKDOWN = "{(technology,gas),(company,rhonepower)}"
_MISSING_COUNTRY_TECH_BREAKDOWN = "{(country,None),(company,rhonepower),(technology,None)}"


@pytest.fixture()
def property_order_workspace(test_files_root: Path, tmp_path: Path) -> tuple[Path, pl.DataFrame]:
    src = test_files_root / "filtering_and_breakdown_property_order"
    dst = tmp_path / "filtering_and_breakdown_property_order"
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    shutil.copytree(src, dst)
    run_view_building_process(paths_from_dataset(dst), ParquetViewSinker(results_dir))
    view = pl.read_parquet(next(results_dir.glob("view*.parquet")))
    return dst, view


def _assert_totals_close(got: pl.DataFrame, exp: pl.DataFrame, *, msg: str = "") -> None:
    merged = got.join(exp, on="scenario_id", how="inner")
    assert merged.height == exp.height, msg
    raw_max = (merged["view_total"] - merged["expected_total"]).abs().max()
    assert isinstance(raw_max, Real), f"{msg} unexpected max diff type: {type(raw_max)}"
    max_diff = float(raw_max)
    assert max_diff < 1e-6, f"{msg} max_abs_diff={max_diff}"


def test_generators_with_same_properties_share_one_breakdown_key(
    property_order_workspace: tuple[Path, pl.DataFrame],
) -> None:
    """
    gas_1 declares technology then company; gas_2 declares company then technology.
    Aggregated rows for (gas, rhonepower) must use a single breakdown_properties value (no split groups).
    """
    _, view = property_order_workspace
    rows = view.filter(pl.col("metric_id") == "PRODUCTION_BY_TECH_AND_COMPANY")
    gas_rhonepower_rows = rows.filter(
        pl.col("breakdown_properties").str.contains("gas") & pl.col("breakdown_properties").str.contains("rhonepower")
    )
    assert gas_rhonepower_rows.height > 0
    breakdown_values = set(gas_rhonepower_rows["breakdown_properties"].unique().to_list())
    assert breakdown_values == {_GAS_RHONEPOWER_BREAKDOWN}


def test_same_breakdown_group_sums_all_matching_generators(property_order_workspace: tuple[Path, pl.DataFrame]) -> None:
    """Per scenario, the (gas, rhonepower) view bucket must equal the sum of gas_1 and gas_2 generation."""
    dataset_dir, view = property_order_workspace
    sim = pl.read_parquet(next(dataset_dir.glob("simulation_table.parquet")))

    expected = (
        sim.filter((pl.col("output") == "generation") & pl.col("component").is_in(_GAS_RHONEPOWER_GENERATORS))
        .group_by("scenario_index")
        .agg(pl.col("value").sum().alias("expected_total"))
        .rename({"scenario_index": "scenario_id"})
        .sort("scenario_id")
    )

    got = (
        view.filter(
            (pl.col("metric_id") == "PRODUCTION_BY_TECH_AND_COMPANY")
            & (pl.col("breakdown_properties") == _GAS_RHONEPOWER_BREAKDOWN)
        )
        .group_by("scenario_id")
        .agg(pl.col("metric_value").sum().alias("view_total"))
        .sort("scenario_id")
    )

    _assert_totals_close(got, expected, msg="PRODUCTION_BY_TECH_AND_COMPANY (gas, rhonepower)")


def test_breakdown_missing_property_keys_use_none_literal(test_files_root: Path) -> None:
    """
    gen_company_only declares company only; country and technology are absent.
    Breakdown must list (key,None) for missing keys, not omit them or return "{}".
    """
    root = test_files_root / "filtering_and_breakdown_property_order"
    library_path = root / "libraries" / "library.yml"
    library = load_library(library_path)
    system = load_system(root / "system.yml", resolve_libraries(library_path))
    catalog = load_catalog(root / "catalogs" / "catalog.yml")
    view_config = load_view_config(root / "view_config.yml")
    metric = catalog.get_metric("PRODUCTION_BY_COUNTRY_COMPANY_TECH")

    components = [Component(component) for component in system.components]
    supply_components_with_taxonomy_categories(components, library.taxonomy_category_by_model)
    components_by_taxon = group_components_by_taxon(components)
    component_port_connections = build_component_port_connections(system.connections)
    supply_components_with_port_connections(components, component_port_connections)
    supply_components_with_locations(components_by_taxon, [metric], view_config.location_taxonomy_category)

    table = MetricStructureTableBuilder(
        view_config,
        components_by_taxon,
    ).build(metric)
    df = table.dataframe.collect()
    partial = df.filter(pl.col("component") == "gen_company_only")
    assert partial.height == 1
    assert partial["breakdown_properties"][0] == _MISSING_COUNTRY_TECH_BREAKDOWN

    gas_1 = df.filter(pl.col("component") == "gas_1")
    assert gas_1.height == 1
    assert gas_1["breakdown_properties"][0] == "{(country,None),(company,rhonepower),(technology,gas)}"
