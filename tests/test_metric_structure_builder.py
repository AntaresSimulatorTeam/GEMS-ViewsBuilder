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
from types import SimpleNamespace
from typing import Any

import polars as pl
import pytest

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
from gems_views_builder.input.component import (
    Component,
    build_component_port_connections,
    find_components_taxonomy_categories,
    group_components_by_taxonomy_category,
    save_component_port_connections,
)
from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.metrics_structure_builder import (
    MetricStructureTableBuilder,
    format_metric_location,
)


def build_components_by_taxonomy_category(system: Any, library: Any) -> dict[str, list[Component]]:
    components = [Component(component) for component in system.components]
    find_components_taxonomy_categories(components, library.taxonomy_category_by_model)
    components_by_taxonomy_category = group_components_by_taxonomy_category(components)
    component_port_connections = build_component_port_connections(system.connections)
    save_component_port_connections(components, component_port_connections)
    return components_by_taxonomy_category


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = load_library(test_3 / "library.yml")
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    view_config = load_view_config(test_3 / "view_config.yml")
    components_by_taxonomy_category = build_components_by_taxonomy_category(system, library)
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
        "location_taxonomy_category": view_config.location_taxonomy_category,
        "components_by_taxonomy_category": components_by_taxonomy_category,
        "components_by_id": {
            component.id: component
            for components in components_by_taxonomy_category.values()
            for component in components
        },
    }


def build(metric_id: str, components: dict[str, Any]) -> pl.DataFrame:
    metric = components["catalog"].get_metric(metric_id)
    table = MetricStructureTableBuilder(
        components["location_taxonomy_category"],
        components["components_by_taxonomy_category"],
    ).build(metric)
    return table.dataframe.collect()


def make_component(properties: dict[str, str]) -> Component:
    return Component(SimpleNamespace(id="fake", model=SimpleNamespace(id="lib.model"), properties=properties))


def test_format_breakdown_properties_missing_keys_use_none_literal() -> None:
    breakdown = [
        PropertySchema(key="country"),
        PropertySchema(key="company"),
        PropertySchema(key="technology"),
    ]
    component = make_component({"company": "rhonepower"})
    assert component.format_breakdown_properties(breakdown) == "{(country,None),(company,rhonepower),(technology,None)}"


def test_format_breakdown_properties_all_keys_present() -> None:
    breakdown = [PropertySchema(key="technology"), PropertySchema(key="company")]
    component = make_component({"technology": "gas", "company": "rhonepower"})
    assert component.format_breakdown_properties(breakdown) == "{(technology,gas),(company,rhonepower)}"


def test_format_breakdown_properties_empty_breakdown() -> None:
    component = make_component({"company": "x"})
    assert component.format_breakdown_properties(None) == "{}"


def test_format_metric_location_single() -> None:
    assert format_metric_location("busA") == "busA"


def test_format_metric_location_multiple() -> None:
    assert format_metric_location(("busA", "busB")) == "(busA,busB)"


def test_format_metric_location_preserves_duplicates() -> None:
    assert format_metric_location(("busA", "busA")) == "(busA,busA)"


def test_format_metric_location_empty() -> None:
    assert format_metric_location(()) == "()"


def _parse_metric_location(encoded: str) -> list[str]:
    if encoded.startswith("(") and encoded.endswith(")"):
        inner = encoded[1:-1]
        return [] if not inner else [part.strip() for part in inner.split(",")]
    return [encoded.strip('"')]


def _component_matches_filters(metric_filter: PropertySchema | None, component: Component) -> bool:
    """Match the filter clause against component properties."""
    return component.match(metric_filter)


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def _count_expected_rows(metric_id: str, component_ids: list[str], components: dict[str, Any]) -> int:
    metric = components["catalog"].get_metric(metric_id)
    components_by_id = components["components_by_id"]
    count = 0
    for cid in component_ids:
        if _component_matches_filters(metric.filter, components_by_id[cid]):
            count += len(metric.terms)
    return count


def test_prod_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = build("PROD", test_3_components)
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    assert len(df) == _count_expected_rows("PROD", candidates, test_3_components)


def test_prod_structure_components(test_3_components: dict[str, Any]) -> None:
    df = build("PROD", test_3_components)
    metric = test_3_components["catalog"].get_metric("PROD")
    components_by_id = test_3_components["components_by_id"]
    candidates = ["generator_A1", "generator_A2", "generator_B1"]
    expected = {cid for cid in candidates if _component_matches_filters(metric.filter, components_by_id[cid])}
    assert set(df["component"].to_list()) == expected


def test_prod_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = build("PROD", test_3_components)
    components_by_id = test_3_components["components_by_id"]
    for comp in ("generator_A1", "generator_A2", "generator_B1"):
        comp_rows = df.filter(pl.col("component") == comp)
        if len(comp_rows) == 0:
            continue
        resolved = components_by_id[comp].get_location("p_balance_port")
        assert comp_rows["metric_location"].to_list() == [format_metric_location(resolved)]


def test_prod_structure_output(test_3_components: dict[str, Any]) -> None:
    df = build("PROD", test_3_components)
    if len(df) == 0:
        return
    assert set(df["output"].to_list()) == {"p"}


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = build("LOAD", test_3_components)
    assert len(df) == _count_expected_rows("LOAD", ["load_AL"], test_3_components)


def test_load_structure_component_and_location(
    test_3_components: dict[str, Any],
) -> None:
    df = build("LOAD", test_3_components)
    if len(df) == 0:
        return
    component_rows = df.filter(pl.col("component") == "load_AL")
    assert len(component_rows) == 1
    assert component_rows["metric_location"][0] == "busA"
    assert set(component_rows["output"].to_list()) == {"active_load"}


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_structure_row_count(test_3_components: dict[str, Any]) -> None:
    df = build("BALANCE", test_3_components)
    assert len(df) == _count_expected_rows("BALANCE", ["link_link_AB"], test_3_components)


def test_balance_structure_locations(test_3_components: dict[str, Any]) -> None:
    df = build("BALANCE", test_3_components)
    if len(df) == 0:
        return
    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert link_rows.filter(pl.col("output") == "p0_port.flow")["metric_location"][0] == "busA"
    assert link_rows.filter(pl.col("output") == "p1_port.flow")["metric_location"][0] == "busB"


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = build("BALANCE", test_3_components)
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
            test_3_components["location_taxonomy_category"],
            test_3_components["components_by_taxonomy_category"],
        ).build(metric)


def test_get_location_tuple_of_ports_returns_peer_per_port(test_3_components: dict[str, Any]) -> None:
    """Each port in a location_ports tuple resolves to its connected peer(s)."""
    components_by_id = test_3_components["components_by_id"]
    locations = components_by_id["link_link_AB"].get_location(("p0_port", "p1_port"))
    assert isinstance(locations, tuple)
    assert locations == ("busA", "busB")


def test_tuple_location_ports_produces_one_row_per_location(test_3_components: dict[str, Any]) -> None:
    """A term with multiple location_ports yields one row with all resolved locations merged."""
    components_by_id = test_3_components["components_by_id"]
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
    table = MetricStructureTableBuilder(
        test_3_components["location_taxonomy_category"],
        test_3_components["components_by_taxonomy_category"],
    ).build(metric)
    df = table.dataframe.collect()

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == format_metric_location(
        components_by_id["link_link_AB"].get_location(("p0_port", "p1_port"))
    )
    assert set(_parse_metric_location(link_rows["metric_location"][0])) == {"busA", "busB"}
    assert set(link_rows["output"].to_list()) == {"p0_port.flow"}


def test_two_ports_resolving_to_same_peer_keep_duplicate_locations_in_single_row(test_files_root: Path) -> None:
    """When two ports resolve to the same peer, the single structure row keeps both locations (busA twice)."""
    test_3 = test_files_root / "test_3"
    library = load_library(test_3 / "library.yml")
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    components_by_taxonomy_category = build_components_by_taxonomy_category(system, library)
    components_by_id = {
        component.id: component for components in components_by_taxonomy_category.values() for component in components
    }

    # Default test_3 wiring uses p0_port -> busA and p1_port -> busB; force both ports to busA here.
    components_by_id["link_link_AB"].connections["p0_port"] = {"busA"}
    components_by_id["link_link_AB"].connections["p1_port"] = {"busA"}

    assert components_by_id["link_link_AB"].get_location(("p0_port", "p1_port")) == ("busA", "busA")

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
    view_config = load_view_config(test_3 / "view_config.yml")
    table = MetricStructureTableBuilder(
        view_config.location_taxonomy_category,
        components_by_taxonomy_category,
    ).build(metric)
    df = table.dataframe.collect()

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == "(busA,busA)"
    assert _parse_metric_location(link_rows["metric_location"][0]) == ["busA", "busA"]
