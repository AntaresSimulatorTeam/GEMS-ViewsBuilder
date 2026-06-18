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

import polars as pl
import pytest
from gems.study import Component  # type: ignore[import-untyped]

from gems_views_builder.input.catalog import load_catalog
from gems_views_builder.input.library import load_library
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.metrics_builder import (
    MetricStructureBuilder,
    MetricStructureTable,
    _format_breakdown_properties,
    _format_metric_location,
)


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    system = System.from_file(test_3 / "system.yml")
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = load_library(test_3 / "library.yml")
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
    }


def _build(metric_id: str, components: dict[str, Any]) -> "MetricStructureTable":
    metric = components["catalog"].get_metric(metric_id)
    return MetricStructureBuilder(
        components["system"],
        metric,
        components["library"],
    ).build()


def test_format_breakdown_properties_missing_keys_use_none_literal() -> None:
    breakdown = (
        PropertySchema(key="country"),
        PropertySchema(key="company"),
        PropertySchema(key="technology"),
    )
    component_properties = {"company": "rhonepower"}
    assert (
        _format_breakdown_properties(component_properties, breakdown)
        == "{(country,None),(company,rhonepower),(technology,None)}"
    )


def test_format_breakdown_properties_all_keys_present() -> None:
    breakdown = (PropertySchema(key="technology"), PropertySchema(key="company"))
    component_properties = {"technology": "gas", "company": "rhonepower"}
    assert _format_breakdown_properties(component_properties, breakdown) == "{(technology,gas),(company,rhonepower)}"


def test_format_breakdown_properties_empty_breakdown() -> None:
    assert _format_breakdown_properties({"company": "x"}, None) == "{}"


def test_format_metric_location_single() -> None:
    assert _format_metric_location(("busA",)) == "{busA}"


def test_format_metric_location_multiple() -> None:
    assert _format_metric_location(("busA", "busB")) == "{busA,busB}"


def test_format_metric_location_preserves_duplicates() -> None:
    assert _format_metric_location(("busA", "busA")) == "{busA,busA}"


def test_format_metric_location_empty() -> None:
    assert _format_metric_location(()) == "{}"


def _parse_metric_location(encoded: str) -> list[str]:
    assert encoded.startswith("{") and encoded.endswith("}")
    inner = encoded[1:-1]
    return [] if not inner else inner.split(",")


def _component_matches_filters(metric_filter: PropertySchema | None, component: Component) -> bool:
    """Match the filter clause against component properties."""
    if metric_filter is None:
        return True
    return bool(component.properties.get(metric_filter.key) == metric_filter.value)


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def _count_expected_rows(metric_id: str, component_ids: list[str], components: dict[str, Any]) -> int:
    metric = get_catalog_metric(components["catalog"], metric_id)
    system = components["system"]
    count = 0
    for cid in component_ids:
        if _component_matches_filters(metric.filter, system.get_component(cid)):
            count += len(metric.terms)
    return count


def test_prod_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    assert len(df) == _count_expected_rows("PROD", candidates, test_3_components)


def test_prod_structure_components(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    metric = get_catalog_metric(test_3_components["catalog"], "PROD")
    system = test_3_components["system"]
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    expected = {cid for cid in candidates if _component_matches_filters(metric.filter, system.get_component(cid))}
    assert set(df["component"].to_list()) == expected


def test_prod_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components).dataframe
    system = test_3_components["system"]
    for comp in ("generator_A1", "generator_A2", "generator_B1"):
        comp_rows = df.filter(pl.col("component") == comp)
        if len(comp_rows) == 0:
            continue
        resolved = system.get_location(comp, "p_balance_port")
        raw_locations = (resolved,) if isinstance(resolved, str) else resolved
        assert comp_rows["metric_location"].to_list() == [_format_metric_location(raw_locations)]


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
    assert len(df) == _count_expected_rows("LOAD", ["load_AL"], test_3_components)


def test_load_structure_component_and_location(
    test_3_components: dict[str, Any],
) -> None:
    df = _build("LOAD", test_3_components).dataframe
    if len(df) == 0:
        return
    component_rows = df.filter(pl.col("component") == "load_AL")
    assert len(component_rows) == 1
    assert component_rows["metric_location"][0] == "{busA}"
    assert set(component_rows["output"].to_list()) == {"active_load"}


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    assert len(df) == _count_expected_rows("BALANCE", ["link_link_AB"], test_3_components)


def test_balance_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    if len(df) == 0:
        return
    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert link_rows.filter(pl.col("output") == "p0_port.flow")["metric_location"][0] == "{busA}"
    assert link_rows.filter(pl.col("output") == "p1_port.flow")["metric_location"][0] == "{busB}"


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    if len(df) == 0:
        return
    assert set(df["component"].to_list()) == {"link_link_AB"}


# ---------------------------------------------------------------------------
# Multiple locations merged into a single row (from filtering branch, adapted)
# ---------------------------------------------------------------------------


def test_single_port_multiple_peers_produces_one_row_per_peer(test_3_components: dict[str, Any]) -> None:
    """A term with a single location_port that connects to multiple peers yields one merged row.

    In test_3, busA.p_balance_port connects to generator_A1, generator_A2, load_AL, link_link_AB
    and busB.p_balance_port connects to generator_B1, link_link_AB.
    All peers for each bus are encoded in a single metric_location value.
    """
    system = test_3_components["system"]
    metric = Metric(
        id="BUS_PEER_TEST",
        terms=[
            Term(
                taxonomy_category="balance",
                output_id="p_balance_port.flow",
                location_ports="p_balance_port",
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    df = (
        MetricStructureBuilder(
            test_3_components["system"],
            test_3_components["catalog"],
            metric,
            test_3_components["taxonomy"],
            test_3_components["library"],
        )
        .build()
        .dataframe
    )

    bus_a_expected = {"generator_A1", "generator_A2", "load_AL", "link_link_AB"}
    bus_a_rows = df.filter(pl.col("component") == "busA")
    assert len(bus_a_rows) == 1
    assert bus_a_rows["metric_location"][0] == _format_metric_location(system.get_location("busA", "p_balance_port"))
    assert set(_parse_metric_location(bus_a_rows["metric_location"][0])) == bus_a_expected

    bus_b_expected = {"generator_B1", "link_link_AB"}
    bus_b_rows = df.filter(pl.col("component") == "busB")
    assert len(bus_b_rows) == 1
    assert bus_b_rows["metric_location"][0] == _format_metric_location(system.get_location("busB", "p_balance_port"))
    assert set(_parse_metric_location(bus_b_rows["metric_location"][0])) == bus_b_expected


def test_get_location_tuple_of_ports_returns_peer_per_port(test_3_components: dict[str, Any]) -> None:
    """Each port in a location_ports tuple resolves to its connected peer(s)."""
    system = test_3_components["system"]
    locations = system.get_location("link_link_AB", ("p0_port", "p1_port"))
    assert isinstance(locations, tuple)
    assert locations == ("busA", "busB")


def test_tuple_location_ports_produces_one_row_per_location(test_3_components: dict[str, Any]) -> None:
    """A term with multiple location_ports yields one row with all resolved locations merged."""
    system = test_3_components["system"]
    metric = Metric(
        id="LINK_BOTH_PORTS",
        terms=[
            Term(
                taxonomy_category="link",
                output_id="p0_port.flow",
                location_ports=("p0_port", "p1_port"),
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    df = (
        MetricStructureBuilder(
            test_3_components["system"],
            test_3_components["catalog"],
            metric,
            test_3_components["taxonomy"],
            test_3_components["library"],
        )
        .build()
        .dataframe
    )

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == _format_metric_location(
        system.get_location("link_link_AB", ("p0_port", "p1_port"))
    )
    assert set(_parse_metric_location(link_rows["metric_location"][0])) == {"busA", "busB"}
    assert set(link_rows["output"].to_list()) == {"p0_port.flow"}


def test_duplicate_locations_from_two_ports_produce_duplicate_rows(test_files_root: Path) -> None:
    """When two ports resolve to the same peer, get_location and the structure table keep both entries."""
    test_3 = test_files_root / "test_3"
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = ModelLibrary.load(test_3 / "library.yml")
    system = InputSystem.load(test_3 / "system.yml", library)
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")

    # Default test_3 wiring uses p0_port -> busA and p1_port -> busB; force both ports to busA here.
    system._component_port_connections[("link_link_AB", "p0_port")] = {"busA"}
    system._component_port_connections[("link_link_AB", "p1_port")] = {"busA"}

    assert system.get_location("link_link_AB", ("p0_port", "p1_port")) == ("busA", "busA")

    metric = Metric(
        id="DUP_PEER_VIA_TWO_PORTS",
        terms=[
            Term(
                taxonomy_category="link",
                output_id="p0_port.flow",
                location_ports=("p0_port", "p1_port"),
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    df = MetricStructureBuilder(system, catalog, metric, taxonomy, library).build().dataframe

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == "{busA,busA}"
    assert _parse_metric_location(link_rows["metric_location"][0]) == ["busA", "busA"]
