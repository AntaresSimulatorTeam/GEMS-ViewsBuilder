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

from gems_views_builder.catalog import (
    Metric,
    PropertySchema,
    Term,
    TermsOperator,
    TimeOperator,
    get_catalog_metric,
    load_catalog,
)
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics import LocationAggregation
from gems_views_builder.metrics_builder import (
    MetricStructureBuilder,
    MetricStructureTable,
    _format_breakdown_properties,
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


def _component_matches_filters(metric_filter: tuple[PropertySchema, ...] | None, component: Component) -> bool:
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


def _count_expected_rows(metric_id: str, component_ids: list[str], components: dict[str, Any]) -> int:
    metric = get_catalog_metric(components["catalog"], metric_id)
    system = components["system"]
    count = 0
    for cid in component_ids:
        if _component_matches_filters(metric.filter, system.get_component(cid)):
            for term in metric.terms:
                loc = system.get_location(cid, term.location_ports)
                count += 1 if isinstance(loc, str) else len(loc)
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
    locations_by_component: dict[str, set[str]] = {}
    for comp, loc in df.select(["component", "metric_location"]).rows():
        locations_by_component.setdefault(comp, set()).add(loc)
    if "generator_A1" in locations_by_component:
        assert "busA" in locations_by_component["generator_A1"]
    if "generator_A2" in locations_by_component:
        assert "busA" in locations_by_component["generator_A2"]
    if "generator_B1" in locations_by_component:
        assert "busB" in locations_by_component["generator_B1"]


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
    assert len(component_rows) >= 1
    assert "busA" in component_rows["metric_location"].to_list()
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
    locations_by_output: dict[str, set[str]] = {}
    for output, loc in df.select(["output", "metric_location"]).rows():
        locations_by_output.setdefault(output, set()).add(loc)
    assert "busA" in locations_by_output["p0_port.flow"]
    assert "busB" in locations_by_output["p1_port.flow"]


def test_balance_structure_component(test_3_components: dict[str, Any]) -> None:
    df = _build("BALANCE", test_3_components).dataframe
    if len(df) == 0:
        return
    assert set(df["component"].to_list()) == {"link_link_AB"}


# ---------------------------------------------------------------------------
# Multiple locations expand into separate rows
# ---------------------------------------------------------------------------


def test_single_port_multiple_peers_produces_one_row_per_peer(test_3_components: dict[str, Any]) -> None:
    """A term with a single location_port that connects to multiple peers yields one row per peer.

    In test_3, busA.p_balance_port connects to generator_A1, generator_A2, load_AL, link_link_AB
    and busB.p_balance_port connects to generator_B1, link_link_AB.
    Each bus should therefore produce as many rows as it has peers.
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
    assert len(bus_a_rows) == len(bus_a_expected)
    assert set(bus_a_rows["metric_location"].to_list()) == bus_a_expected
    assert bus_a_rows["metric_location"].n_unique() == len(bus_a_expected)

    bus_b_expected = {"generator_B1", "link_link_AB"}
    bus_b_rows = df.filter(pl.col("component") == "busB")
    assert len(bus_b_rows) == len(bus_b_expected)
    assert set(bus_b_rows["metric_location"].to_list()) == bus_b_expected
    assert bus_b_rows["metric_location"].n_unique() == len(bus_b_expected)


def test_get_location_tuple_of_ports_returns_peer_per_port(test_3_components: dict[str, Any]) -> None:
    """Each port in a location_ports tuple resolves to its connected peer(s)."""
    system = test_3_components["system"]
    locations = system.get_location("link_link_AB", ("p0_port", "p1_port"))
    assert isinstance(locations, tuple)
    assert set(locations) == {"busA", "busB"}


def test_tuple_location_ports_produces_one_row_per_location(test_3_components: dict[str, Any]) -> None:
    """A term with multiple location_ports yields one metric-structure row per resolved location."""
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
    assert len(link_rows) == 2
    assert set(link_rows["metric_location"].to_list()) == {"busA", "busB"}
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
    assert len(link_rows) == 2
    assert link_rows["metric_location"].to_list() == ["busA", "busA"]
    assert link_rows["metric_location"].n_unique() == 1


# ---------------------------------------------------------------------------
# Location aggregation fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def loc_agg_components(test_files_root: Path) -> dict[str, Any]:
    fixture = test_files_root / "test_location_aggregation"
    library = ModelLibrary.load(fixture / "library.yml")
    system = InputSystem.load(fixture / "system.yml", library)
    catalog = load_catalog(fixture / "catalogs" / "catalog.yml")
    taxonomy = load_taxonomy(fixture / "taxonomy.yml")
    return {"system": system, "catalog": catalog, "library": library, "taxonomy": taxonomy}


def _make_builder(
    components: dict[str, Any],
    location_aggregation: LocationAggregation | None = None,
) -> MetricStructureBuilder:
    metric = get_catalog_metric(components["catalog"], "PRODUCTION")
    return MetricStructureBuilder(
        components["system"],
        components["catalog"],
        metric,
        components["taxonomy"],
        components["library"],
        location_aggregation=location_aggregation,
    )


# ---------------------------------------------------------------------------
# _resolve_location_aggregation unit tests
# ---------------------------------------------------------------------------


def test_resolve_single_location_with_property(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, LocationAggregation(key="country"))
    assert builder._resolve_location_aggregation(["area_FR1"]) == ["FR"]


def test_resolve_multiple_locations(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, LocationAggregation(key="country"))
    assert builder._resolve_location_aggregation(["area_FR1", "area_DE"]) == ["FR", "DE"]


def test_resolve_missing_property_keep(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, LocationAggregation(key="country", on_missing="keep"))
    assert builder._resolve_location_aggregation(["area_orph"]) == ["<unknown>"]


def test_resolve_missing_property_drop(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, LocationAggregation(key="country", on_missing="drop"))
    assert builder._resolve_location_aggregation(["area_orph"]) == []


def test_resolve_mixed_known_and_unknown_drop(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, LocationAggregation(key="country", on_missing="drop"))
    assert builder._resolve_location_aggregation(["area_FR1", "area_orph"]) == ["FR"]


def test_resolve_no_aggregation_passthrough(loc_agg_components: dict[str, Any]) -> None:
    builder = _make_builder(loc_agg_components, location_aggregation=None)
    assert builder._resolve_location_aggregation(["area_FR1"]) == ["area_FR1"]


# ---------------------------------------------------------------------------
# Location aggregation wired through build()
# ---------------------------------------------------------------------------


def test_build_with_country_aggregation_collapses_fr(loc_agg_components: dict[str, Any]) -> None:
    """gen_FR1 and gen_FR2 both resolve to 'FR' via the country property."""
    metric = get_catalog_metric(loc_agg_components["catalog"], "PRODUCTION")
    df = (
        MetricStructureBuilder(
            loc_agg_components["system"],
            loc_agg_components["catalog"],
            metric,
            loc_agg_components["taxonomy"],
            loc_agg_components["library"],
            location_aggregation=LocationAggregation(key="country"),
        )
        .build()
        .dataframe
    )
    fr_rows = df.filter(pl.col("metric_location") == "FR")
    assert set(fr_rows["component"].to_list()) == {"gen_FR1", "gen_FR2"}
    assert df.filter(pl.col("metric_location").is_in(["area_FR1", "area_FR2"])).is_empty()


def test_build_with_drop_excludes_orphan(loc_agg_components: dict[str, Any]) -> None:
    """gen_orph has no country property; on_missing=drop excludes it."""
    metric = get_catalog_metric(loc_agg_components["catalog"], "PRODUCTION")
    df = (
        MetricStructureBuilder(
            loc_agg_components["system"],
            loc_agg_components["catalog"],
            metric,
            loc_agg_components["taxonomy"],
            loc_agg_components["library"],
            location_aggregation=LocationAggregation(key="country", on_missing="drop"),
        )
        .build()
        .dataframe
    )
    assert "gen_orph" not in df["component"].to_list()
    assert "<unknown>" not in df["metric_location"].to_list()


def test_build_multiport_location_ports_with_aggregation(loc_agg_components: dict[str, Any]) -> None:
    """A term with location_ports=(p0_port, p1_port) on link_FRDE produces
    one row per endpoint ('FR' and 'DE') after country aggregation."""
    metric = Metric(
        id="LINK_COUNTRY_TEST",
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
            loc_agg_components["system"],
            loc_agg_components["catalog"],
            metric,
            loc_agg_components["taxonomy"],
            loc_agg_components["library"],
            location_aggregation=LocationAggregation(key="country"),
        )
        .build()
        .dataframe
    )
    link_rows = df.filter(pl.col("component") == "link_FRDE")
    assert set(link_rows["metric_location"].to_list()) == {"FR", "DE"}
    assert "area_FR1" not in link_rows["metric_location"].to_list()
    assert "area_DE" not in link_rows["metric_location"].to_list()
