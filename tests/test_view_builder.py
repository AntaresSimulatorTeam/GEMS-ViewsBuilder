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

import shutil
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.catalog import PropertySchema, get_catalog_metric, load_catalog
from gems_views_builder.library import ModelLibrary
from gems_views_builder.system import InputSystem
from gems_views_builder.views import ViewBuilder


@pytest.fixture()
def view_run(test_files_root: Path, tmp_path: Path) -> tuple[pl.DataFrame, Path]:
    """
    Run ViewBuilder.build() on a fresh copy of test_3 and return the result DataFrame.
    A copy is used so ViewBuilder's intermediate writes do not pollute the shared
    session-scoped test_files_root directory.
    """
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)
    ViewBuilder(dst).build()
    result_file = next((dst / "results").glob("*.parquet"))
    return pl.read_parquet(result_file), dst


def _component_matches_filters(metric_filter: tuple[PropertySchema, ...] | None, component: object) -> bool:
    if metric_filter is None:
        return True
    raw_props = getattr(component, "properties", None) or {}
    if isinstance(raw_props, dict):
        props = raw_props
    else:
        props = {}
        for item in raw_props:
            if isinstance(item, dict):
                pid = item.get("id") or item.get("key")
                pval = item.get("value")
            else:
                pid = getattr(item, "id", None) or getattr(item, "key", None)
                pval = getattr(item, "value", None)
            if isinstance(pid, str):
                props[pid] = pval
    return all(props.get(c.key) == c.value for c in metric_filter)


def _metric_at(df: pl.DataFrame, metric_id: str, location: str) -> pl.DataFrame:
    return df.filter((pl.col("metric_id") == metric_id) & (pl.col("metric_location") == location)).sort("view_date")


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def test_prod_busa_row_count(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "PROD", "busA")

    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    included = [
        cid
        for cid in ("generator_A1", "generator_A2")
        if _component_matches_filters(metric.filter, system.get_component(cid))
    ]
    if not included:
        assert len(rows) == 0
        return
    # one row per timestep t in {1, ..., 24}
    assert len(rows) == 24


def test_prod_busa_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # generator_A1.p(t) + generator_A2.p(t) = t + t = 2t
    rows = _metric_at(view_result, "PROD", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    included = [
        cid
        for cid in ("generator_A1", "generator_A2")
        if _component_matches_filters(metric.filter, system.get_component(cid))
    ]
    if not included:
        assert rows.is_empty()
        return
    multiplier = len(included)
    expected = [multiplier * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_prod_busb_row_count(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "PROD", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("generator_B1")):
        assert len(rows) == 0
        return
    assert len(rows) == 24


def test_prod_busb_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # generator_B1.p(t) = 100 - 2t
    rows = _metric_at(view_result, "PROD", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("generator_B1")):
        assert rows.is_empty()
        return
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_busa_value(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "LOAD", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "LOAD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("load_AL")):
        assert len(rows) == 0
        return
    assert len(rows) == 1
    assert rows["metric_value"][0] == 100


def test_load_busb_absent(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, _ = view_run
    # No consumption component connected to busB
    rows = _metric_at(view_result, "LOAD", "busB")
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_busa_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # link_link_AB.p0_port.flow(t) = 100 - 2t (outflow from busA)
    rows = _metric_at(view_result, "BALANCE", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "BALANCE")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("link_link_AB")):
        assert len(rows) == 0
        return
    assert len(rows) == 24
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_balance_busb_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # link_link_AB.p1_port.flow(t) = -(100 - 2t) (inflow into busB)
    rows = _metric_at(view_result, "BALANCE", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "BALANCE")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("link_link_AB")):
        assert len(rows) == 0
        return
    assert len(rows) == 24
    expected = [-(100 - 2 * t) for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_pipeline_logs_are_saved_to_file(view_run: tuple[pl.DataFrame, Path]) -> None:
    _, dst = view_run
    log_files = list((dst / "logs").glob("pipeline-*.log"))
    assert len(log_files) == 1

    content = log_files[0].read_text(encoding="utf-8")
    assert "[pipeline]" in content
    assert "Starting pipeline for study" in content
    assert "Pipeline complete" in content


def test_reused_view_builder_creates_one_log_file_per_run(test_files_root: Path, tmp_path: Path) -> None:
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    builder = ViewBuilder(dst)
    builder.build()
    builder.build()

    log_files = sorted((dst / "logs").glob("pipeline-*.log"))
    assert len(log_files) == 2

    for log_file in log_files:
        content = log_file.read_text(encoding="utf-8")
        assert "Starting pipeline for study" in content
        assert "Pipeline complete" in content
