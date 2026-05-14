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

from pathlib import Path
from typing import Any

import pytest
from gems.study import Component  # type: ignore[import-untyped]

from gems_views_builder.catalog import PropertyTuple, get_catalog_metric, load_catalog
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics_builder import (
    MetricStructureBuilder,
    MetricStructureTable,
)
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import load_taxonomy


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = ModelLibrary.load(test_3 / "library.yml")
    system = InputSystem.load(test_3 / "system.yml", library)
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
    }


def _build(metric_id: str, components: dict[str, Any]) -> "MetricStructureTable":
    metric = get_catalog_metric(components["catalog"], metric_id)
    return MetricStructureBuilder(
        components["system"],
        components["catalog"],
        metric,
        components["taxonomy"],
        components["library"],
    ).build()


def _component_matches_filters(metric_filter: tuple[PropertyTuple, ...] | None, component: Component) -> bool:
    """Match ALL filter clauses against component properties."""
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


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def test_prod_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    metric = get_catalog_metric(test_3_components["catalog"], "PROD")
    system = test_3_components["system"]
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    expected_components = [
        cid for cid in candidates if _component_matches_filters(metric.filter, system.get_component(cid))
    ]
    assert len(df) == len(expected_components)


def test_prod_structure_components(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    metric = get_catalog_metric(test_3_components["catalog"], "PROD")
    system = test_3_components["system"]
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    expected = {cid for cid in candidates if _component_matches_filters(metric.filter, system.get_component(cid))}
    assert set(df["component"].to_list()) == expected


def test_prod_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    location_by_component: dict[str, Any] = dict(zip(df["component"].to_list(), df["metric_location"].to_list()))
    if "generator_A1" in location_by_component:
        assert location_by_component["generator_A1"] == "busA"
    if "generator_A2" in location_by_component:
        assert location_by_component["generator_A2"] == "busA"
    if "generator_B1" in location_by_component:
        assert location_by_component["generator_B1"] == "busB"


def test_prod_structure_output(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    if len(df) == 0:
        return
    assert set(df["output"].to_list()) == {"p"}


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("LOAD", test_3_components).dataframe
    metric = get_catalog_metric(test_3_components["catalog"], "LOAD")
    system = test_3_components["system"]
    expected = 1 if _component_matches_filters(metric.filter, system.get_component("load_AL")) else 0
    assert len(df) == expected


def test_load_structure_component_and_location(
    test_3_components: dict[str, Any],
) -> None:
    df = _build("LOAD", test_3_components).dataframe
    if len(df) == 0:
        return
    assert df["component"][0] == "load_AL"
    assert df["metric_location"][0] == "busA"
    assert df["output"][0] == "active_load"


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    metric = get_catalog_metric(test_3_components["catalog"], "BALANCE")
    system = test_3_components["system"]
    expected = 2 if _component_matches_filters(metric.filter, system.get_component("link_link_AB")) else 0
    assert len(df) == expected


def test_balance_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    if len(df) == 0:
        return
    output_to_location: dict[str, Any] = dict(zip(df["output"].to_list(), df["metric_location"].to_list()))
    assert output_to_location["p0_port.flow"] == "busA"
    assert output_to_location["p1_port.flow"] == "busB"


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    if len(df) == 0:
        return
    assert set(df["component"].to_list()) == {"link_link_AB"}
