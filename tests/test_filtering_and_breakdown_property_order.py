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

"""Regression tests: component property declaration order must not affect breakdown groupby."""

from __future__ import annotations

import shutil
from numbers import Real
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder import (
    Loader,
    MetricStructureBuilder,
    ViewBuilder,
    load_catalog,
    load_library,
    load_system,
)

# Same (technology, company) as filtering_and_breakdown, but YAML property order differs per component.
_GAS_RHONEPOWER_GENERATORS = ("gas_1", "gas_2")
_GAS_RHONEPOWER_BREAKDOWN = "{(technology,gas),(company,rhonepower)}"
_MISSING_COUNTRY_TECH_BREAKDOWN = "{(country,None),(company,rhonepower),(technology,None)}"


@pytest.fixture()
def property_order_workspace(test_files_root: Path, tmp_path: Path) -> tuple[Path, pl.DataFrame]:
    src = test_files_root / "filtering_and_breakdown_property_order"
    dst = tmp_path / "filtering_and_breakdown_property_order"
    shutil.copytree(src, dst)
    merged = ViewBuilder(Loader(dst).load()).build()
    assert merged.file is not None
    return dst, pl.read_parquet(merged.file)


def _assert_totals_close(got: pl.DataFrame, exp: pl.DataFrame, *, msg: str = "") -> None:
    merged = got.join(exp, on="scenario", how="inner")
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
    sim = pl.read_parquet(dataset_dir / "simulation_table.parquet")

    expected = (
        sim.filter((pl.col("output") == "generation") & pl.col("component").is_in(_GAS_RHONEPOWER_GENERATORS))
        .group_by("scenario_index")
        .agg(pl.col("value").sum().alias("expected_total"))
        .rename({"scenario_index": "scenario"})
        .sort("scenario")
    )

    got = (
        view.filter(
            (pl.col("metric_id") == "PRODUCTION_BY_TECH_AND_COMPANY")
            & (pl.col("breakdown_properties") == _GAS_RHONEPOWER_BREAKDOWN)
        )
        .group_by("scenario")
        .agg(pl.col("metric_value").sum().alias("view_total"))
        .sort("scenario")
    )

    _assert_totals_close(got, expected, msg="PRODUCTION_BY_TECH_AND_COMPANY (gas, rhonepower)")


def test_breakdown_missing_property_keys_use_none_literal(test_files_root: Path) -> None:
    """
    gen_company_only declares company only; country and technology are absent.
    Breakdown must list (key,None) for missing keys, not omit them or return "{}".
    """
    root = test_files_root / "filtering_and_breakdown_property_order"
    library = load_library(root / "library.yml")
    system = load_system(root)
    catalog = load_catalog(root / "catalogs" / "catalog.yml")
    metric = catalog.get_metric("PRODUCTION_BY_COUNTRY_COMPANY_TECH")

    df = MetricStructureBuilder(system, metric, library).build().dataframe
    partial = df.filter(pl.col("component") == "gen_company_only")
    assert partial.height == 1
    assert partial["breakdown_properties"][0] == _MISSING_COUNTRY_TECH_BREAKDOWN

    gas_1 = df.filter(pl.col("component") == "gas_1")
    assert gas_1.height == 1
    assert gas_1["breakdown_properties"][0] == "{(country,None),(company,rhonepower),(technology,gas)}"
