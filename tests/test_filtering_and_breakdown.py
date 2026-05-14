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

"""Regression tests for catalog filter and breakdown against ``filtering_and_breakdown``."""

from __future__ import annotations

import math
import shutil
from numbers import Real
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.views import ViewBuilder

# Generator instances in ``filtering_and_breakdown/system.yml`` (technology, company).
_FILTERING_AND_BREAKDOWN_GEN_META: dict[str, tuple[str, str]] = {
    "nuclear_1": ("nuclear", "rhonepower"),
    "nuclear_2": ("nuclear", "britishnuke"),
    "gas_1": ("gas", "rhonepower"),
    "gas_2": ("gas", "rhonepower"),
}


@pytest.fixture()
def filtering_and_breakdown_workspace(test_files_root: Path, tmp_path: Path) -> tuple[Path, pl.DataFrame]:
    """
    Copy ``filtering_and_breakdown``, run ``ViewBuilder``, return ``(dataset_dir, view_df)``.
    """
    src = test_files_root / "filtering_and_breakdown"
    dst = tmp_path / "filtering_and_breakdown"
    shutil.copytree(src, dst)
    ViewBuilder(dst).build()
    result_file = next((dst / "results").glob("*.parquet"))
    return dst, pl.read_parquet(result_file)


@pytest.fixture()
def fb_view_result(filtering_and_breakdown_workspace: tuple[Path, pl.DataFrame]) -> pl.DataFrame:
    return filtering_and_breakdown_workspace[1]


def _at(df: pl.DataFrame, metric_id: str) -> pl.DataFrame:
    return df.filter(pl.col("metric_id") == metric_id)


def _view_generation_total_by_scenario(
    view: pl.DataFrame, metric_id: str, *, breakdown_properties: str | None
) -> pl.DataFrame:
    df = _at(view, metric_id)
    if breakdown_properties is not None:
        df = df.filter(pl.col("breakdown_properties") == breakdown_properties)
    return df.group_by("scenario").agg(pl.col("metric_value").sum().alias("view_total")).sort("scenario")


def _assert_totals_close(got: pl.DataFrame, exp: pl.DataFrame, *, msg: str = "") -> None:
    merged = got.join(exp, on="scenario", how="inner")
    assert merged.height == exp.height, msg
    raw_max = (merged["view_total"] - merged["expected_total"]).abs().max()
    assert isinstance(raw_max, Real), f"{msg} unexpected max diff type: {type(raw_max)}"
    max_diff = float(raw_max)
    assert max_diff < 1e-6, f"{msg} max_abs_diff={max_diff}"


def _expected_generation_total_by_scenario(
    sim: pl.DataFrame, *, technology: str | None = None, company: str | None = None
) -> pl.DataFrame:
    rows = [
        {"component": cid, "technology": t, "company": c} for cid, (t, c) in _FILTERING_AND_BREAKDOWN_GEN_META.items()
    ]
    meta = pl.DataFrame(rows)
    base = sim.filter(
        (pl.col("output") == "generation") & pl.col("component").is_in(list(_FILTERING_AND_BREAKDOWN_GEN_META))
    ).join(meta, on="component", how="inner")
    if technology is not None:
        base = base.filter(pl.col("technology") == technology)
    if company is not None:
        base = base.filter(pl.col("company") == company)
    return (
        base.group_by("scenario_index")
        .agg(pl.col("value").sum().alias("expected_total"))
        .rename({"scenario_index": "scenario"})
        .sort("scenario")
    )


def test_breakdown_format_single_key(fb_view_result: pl.DataFrame) -> None:
    """
    PRODUCTION_BY_TECH should include two breakdown buckets: nuclear and gas.
    """
    rows = _at(fb_view_result, "PRODUCTION_BY_TECH")
    assert rows.height > 0
    bds = set(rows["breakdown_properties"].unique().to_list())
    assert "{(technology,nuclear)}" in bds
    assert "{(technology,gas)}" in bds


def test_breakdown_format_multi_key(fb_view_result: pl.DataFrame) -> None:
    rows = _at(fb_view_result, "PRODUCTION_BY_TECH_AND_COMPANY")
    assert rows.height > 0
    bds = set(rows["breakdown_properties"].unique().to_list())
    # Expected combinations in the dataset
    assert "{(technology,nuclear),(company,rhonepower)}" in bds
    assert "{(technology,nuclear),(company,britishnuke)}" in bds
    assert "{(technology,gas),(company,rhonepower)}" in bds


def test_filter_nuclear_production_is_subset_of_by_tech(fb_view_result: pl.DataFrame) -> None:
    """
    NUCLEAR_PRODUCTION is filtered (technology=nuclear), so it must equal the
    PRODUCTION_BY_TECH slice at breakdown {(technology,nuclear)}.
    """
    nuclear = _at(fb_view_result, "NUCLEAR_PRODUCTION").select(
        ["metric_location", "view_date", "scenario", "metric_value"]
    )
    by_tech_nuclear = (
        _at(fb_view_result, "PRODUCTION_BY_TECH")
        .filter(pl.col("breakdown_properties") == "{(technology,nuclear)}")
        .select(["metric_location", "view_date", "scenario", "metric_value"])
    )
    assert nuclear.sort(nuclear.columns).to_dicts() == by_tech_nuclear.sort(by_tech_nuclear.columns).to_dicts()


def test_production_equals_sum_by_tech_and_company_partitions(fb_view_result: pl.DataFrame) -> None:
    """
    For each (location, date, scenario), PRODUCTION must equal the sum across the
    breakdown partitions (tech, company, and tech+company).
    """
    keys = ["metric_location", "view_date", "scenario"]

    prod = _at(fb_view_result, "PRODUCTION").group_by(keys).agg(pl.col("metric_value").sum().alias("v"))

    by_tech = _at(fb_view_result, "PRODUCTION_BY_TECH").group_by(keys).agg(pl.col("metric_value").sum().alias("v"))
    by_company = (
        _at(fb_view_result, "PRODUCTION_BY_COMPANY").group_by(keys).agg(pl.col("metric_value").sum().alias("v"))
    )
    by_both = (
        _at(fb_view_result, "PRODUCTION_BY_TECH_AND_COMPANY")
        .group_by(keys)
        .agg(pl.col("metric_value").sum().alias("v"))
    )

    for other in (by_tech, by_company, by_both):
        joined = prod.join(other, on=keys, how="inner", suffix="_other").sort(keys)
        assert joined["v"].to_list() == joined["v_other"].to_list()


def test_production_by_technology_matches_simulation(
    filtering_and_breakdown_workspace: tuple[Path, pl.DataFrame],
) -> None:
    """Per scenario, PRODUCTION_BY_TECH nuclear / gas totals match raw ``generation`` sums."""
    dataset_dir, view = filtering_and_breakdown_workspace
    sim = pl.read_parquet(dataset_dir / "simulation_table.parquet")

    for tech, bd in (("nuclear", "{(technology,nuclear)}"), ("gas", "{(technology,gas)}")):
        got = _view_generation_total_by_scenario(view, "PRODUCTION_BY_TECH", breakdown_properties=bd)
        exp = _expected_generation_total_by_scenario(sim, technology=tech)
        _assert_totals_close(got, exp, msg=f"PRODUCTION_BY_TECH {tech}")


def test_production_by_company_matches_simulation(
    filtering_and_breakdown_workspace: tuple[Path, pl.DataFrame],
) -> None:
    """Per scenario, company breakdown totals match simulation sums for that company."""
    dataset_dir, view = filtering_and_breakdown_workspace
    sim = pl.read_parquet(dataset_dir / "simulation_table.parquet")

    for company, bd in (
        ("rhonepower", "{(company,rhonepower)}"),
        ("britishnuke", "{(company,britishnuke)}"),
    ):
        got = _view_generation_total_by_scenario(view, "PRODUCTION_BY_COMPANY", breakdown_properties=bd)
        exp = _expected_generation_total_by_scenario(sim, company=company)
        _assert_totals_close(got, exp, msg=f"PRODUCTION_BY_COMPANY {company}")


def test_production_by_technology_and_company_matches_simulation(
    filtering_and_breakdown_workspace: tuple[Path, pl.DataFrame],
) -> None:
    """
    Each (technology, company) bucket is a single generator in this dataset;
    per-scenario totals must match that component's summed ``generation`` in the simulation table.
    """
    dataset_dir, view = filtering_and_breakdown_workspace
    sim = pl.read_parquet(dataset_dir / "simulation_table.parquet")

    cases: tuple[tuple[str, str, str], ...] = (
        ("nuclear", "rhonepower", "{(technology,nuclear),(company,rhonepower)}"),
        ("nuclear", "britishnuke", "{(technology,nuclear),(company,britishnuke)}"),
        ("gas", "rhonepower", "{(technology,gas),(company,rhonepower)}"),
    )
    for technology, company, bd in cases:
        got = _view_generation_total_by_scenario(view, "PRODUCTION_BY_TECH_AND_COMPANY", breakdown_properties=bd)
        exp = _expected_generation_total_by_scenario(sim, technology=technology, company=company)
        _assert_totals_close(got, exp, msg=f"PRODUCTION_BY_TECH_AND_COMPANY {technology=} {company=}")


def test_single_generator_slice_matches_component_simulation_sum(
    filtering_and_breakdown_workspace: tuple[Path, pl.DataFrame],
) -> None:
    """Concrete check: nuclear + rhonepower is only ``nuclear_1`` — compare to its simulation total (scenario 0)."""
    dataset_dir, view = filtering_and_breakdown_workspace
    sim = pl.read_parquet(dataset_dir / "simulation_table.parquet")
    scenario = 0
    expected = (
        sim.filter(
            (pl.col("component") == "nuclear_1")
            & (pl.col("output") == "generation")
            & (pl.col("scenario_index") == scenario)
        )
        .select(pl.col("value").sum())
        .item()
    )
    got = (
        _at(view, "PRODUCTION_BY_TECH_AND_COMPANY")
        .filter(
            (pl.col("breakdown_properties") == "{(technology,nuclear),(company,rhonepower)}")
            & (pl.col("scenario") == scenario)
        )
        .select(pl.col("metric_value").sum())
        .item()
    )
    assert math.isclose(got, expected, rel_tol=0.0, abs_tol=1e-6)
