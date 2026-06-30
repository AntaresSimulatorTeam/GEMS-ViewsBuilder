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

from gems_views_builder import (
    Metric,
    PropertySchema,
    Term,
    TermsOperator,
    TimeOperator,
    load_catalog,
    load_library,
    load_taxonomy,
)
from gems_views_builder.input.system import load_system
from gems_views_builder.metrics_structure_builder import (
    MetricStructureTableBuilder,
    _format_breakdown_properties,
    _format_metric_location,
)


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    system = load_system(test_3)
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = load_library(test_3 / "library.yml")
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
    }


def _build(metric_id: str, components: dict[str, Any]) -> pl.DataFrame:
    metric = components["catalog"].get_metric(metric_id)
    table = MetricStructureTableBuilder(
        components["system"],
        components["library"],
    ).build(metric)
    return table.dataframe.collect()


def test_format_breakdown_properties_missing_keys_use_none_literal() -> None:
    breakdown = [
        PropertySchema(key="country"),
        PropertySchema(key="company"),
        PropertySchema(key="technology"),
    ]
    component_properties = {"company": "rhonepower"}
    assert (
        _format_breakdown_properties(component_properties, breakdown)
        == "{(country,None),(company,rhonepower),(technology,None)}"
    )


def test_format_breakdown_properties_all_keys_present() -> None:
    breakdown = [PropertySchema(key="technology"), PropertySchema(key="company")]
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
    metric = components["catalog"].get_metric(metric_id)
    system = components["system"]
    count = 0
    for cid in component_ids:
        if _component_matches_filters(metric.filter, system.get_component(cid)):
            count += len(metric.terms)
    return count


def test_prod_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components)
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    assert len(df) == _count_expected_rows("PROD", candidates, test_3_components)


def test_prod_structure_components(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components)
    metric = test_3_components["catalog"].get_metric("PROD")
    system = test_3_components["system"]
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    expected = {cid for cid in candidates if _component_matches_filters(metric.filter, system.get_component(cid))}
    assert set(df["component"].to_list()) == expected


def test_prod_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components)
    system = test_3_components["system"]
    for comp in ("generator_A1", "generator_A2", "generator_B1"):
        comp_rows = df.filter(pl.col("component") == comp)
        if len(comp_rows) == 0:
            continue
        resolved = system.get_location(comp, "p_balance_port")
        raw_locations = (resolved,) if isinstance(resolved, str) else resolved
        assert comp_rows["metric_location"].to_list() == [_format_metric_location(raw_locations)]


def test_prod_structure_output(test_3_components: dict[str, Any]) -> None:
    df = _build("PROD", test_3_components)
    if len(df) == 0:
        return
    assert set(df["output"].to_list()) == {"p"}


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = _build("LOAD", test_3_components)
    assert len(df) == _count_expected_rows("LOAD", ["load_AL"], test_3_components)


def test_load_structure_component_and_location(
    test_3_components: dict[str, Any],
) -> None:
    df = _build("LOAD", test_3_components)
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
    df = _build("BALANCE", test_3_components)
    assert len(df) == _count_expected_rows("BALANCE", ["link_link_AB"], test_3_components)


def test_balance_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components)
    if len(df) == 0:
        return
    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert link_rows.filter(pl.col("output") == "p0_port.flow")["metric_location"][0] == "{busA}"
    assert link_rows.filter(pl.col("output") == "p1_port.flow")["metric_location"][0] == "{busB}"


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components)
    if len(df) == 0:
        return
    assert set(df["component"].to_list()) == {"link_link_AB"}


# ---------------------------------------------------------------------------
# Multiple locations merged into a single row (from filtering branch, adapted)
# ---------------------------------------------------------------------------


def test_single_port_multiple_peers_raises(test_3_components: dict[str, Any]) -> None:
    """A single location_port wired to multiple peers is ambiguous and must raise.

    In test_3, busA.p_balance_port connects to generator_A1, generator_A2, load_AL,
    link_link_AB (and busB.p_balance_port to generator_B1, link_link_AB), so resolving
    a single port to a unique locating peer is impossible here.
    """
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
    with pytest.raises(ValueError):
        MetricStructureTableBuilder(
            test_3_components["system"],
            test_3_components["library"],
        ).build(metric)


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
        MetricStructureTableBuilder(
            test_3_components["system"],
            test_3_components["library"],
        )
        .build(metric)
        .dataframe.collect()
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
    library = load_library(test_3 / "library.yml")
    system = load_system(test_3)

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
    df = MetricStructureTableBuilder(system, library).build(metric).dataframe.collect()

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == "{busA,busA}"
    assert _parse_metric_location(link_rows["metric_location"][0]) == ["busA", "busA"]
