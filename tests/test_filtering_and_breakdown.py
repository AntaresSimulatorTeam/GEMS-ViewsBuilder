import shutil
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.views import ViewBuilder


@pytest.fixture()
def fb_view_result(test_files_root: Path, tmp_path: Path) -> pl.DataFrame:
    """
    Run ViewBuilder on the `filtering_and_breakdown` dataset and return the consolidated view.
    """
    src = test_files_root / "filtering_and_breakdown"
    dst = tmp_path / "filtering_and_breakdown"
    shutil.copytree(src, dst)
    ViewBuilder(dst).build()
    result_file = next((dst / "results").glob("*.parquet"))
    return pl.read_parquet(result_file)


def _at(df: pl.DataFrame, metric_id: str) -> pl.DataFrame:
    return df.filter(pl.col("metric_id") == metric_id)


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
    by_company = _at(fb_view_result, "PRODUCTION_BY_COMPANY").group_by(keys).agg(
        pl.col("metric_value").sum().alias("v")
    )
    by_both = _at(fb_view_result, "PRODUCTION_BY_TECH_AND_COMPANY").group_by(keys).agg(
        pl.col("metric_value").sum().alias("v")
    )

    for other in (by_tech, by_company, by_both):
        joined = prod.join(other, on=keys, how="inner", suffix="_other").sort(keys)
        assert joined["v"].to_list() == joined["v_other"].to_list()

