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

from gems_views_builder.catalog import get_catalog_metric, load_catalog
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
    system = InputSystem.from_file(test_3 / "system.yml")
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = ModelLibrary(test_3 / "library.yml")
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


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def test_prod_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    # generator_A1 and generator_A2 at busA, generator_B1 at busB
    assert len(df) == 3


def test_prod_structure_components(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    assert set(df["component"].to_list()) == {
        "generator_A1",
        "generator_A2",
        "generator_B1",
    }


def test_prod_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    location_by_component: dict[str, Any] = dict(zip(df["component"].to_list(), df["metric_location"].to_list()))
    assert location_by_component["generator_A1"] == "busA"
    assert location_by_component["generator_A2"] == "busA"
    assert location_by_component["generator_B1"] == "busB"


def test_prod_structure_output(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    assert set(df["output"].to_list()) == {"p"}


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("LOAD", test_3_components).dataframe
    # Only load_AL (consumption); no store instance in test_3
    assert len(df) == 1


def test_load_structure_component_and_location(
    test_3_components: dict[str, Any],
) -> None:
    df = _build("LOAD", test_3_components).dataframe
    assert df["component"][0] == "load_AL"
    assert df["metric_location"][0] == "busA"
    assert df["output"][0] == "active_load"


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    # link_link_AB contributes one row per term (p0_port → busA, p1_port → busB)
    assert len(df) == 2


def test_balance_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    output_to_location: dict[str, Any] = dict(zip(df["output"].to_list(), df["metric_location"].to_list()))
    assert output_to_location["p0_port.flow"] == "busA"
    assert output_to_location["p1_port.flow"] == "busB"


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    assert set(df["component"].to_list()) == {"link_link_AB"}
