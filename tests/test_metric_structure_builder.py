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
    compute_component_locations,
    find_components_taxonomy_categories,
    format_metric_location,
    group_components_by_taxon,
    save_component_port_connections,
)
from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system
from gems_views_builder.input.view_config import LocationAggregation, load_view_config
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def build_components_by_taxonomy_category(
    system: Any, library: Any, scope_taxon_category: str | None = None
) -> dict[str, list[Component]]:
    components = [Component(component) for component in system.components]
    find_components_taxonomy_categories(components, library.taxonomy_category_by_model)
    components_by_taxon = group_components_by_taxon(components)
    component_port_connections = build_component_port_connections(system.connections)
    save_component_port_connections(components, component_port_connections)
    if scope_taxon_category is not None:
        compute_component_locations(components, scope_taxon_category)
    return components_by_taxon


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = load_library(test_3 / "library.yml")
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    view_config = load_view_config(test_3 / "view_config.yml")
    components_by_taxon = build_components_by_taxonomy_category(system, library, view_config.scope_taxon_category)
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
        "scope_taxon_category": view_config.scope_taxon_category,
        "components_by_taxon": components_by_taxon,
        "components_by_id": {
            component.id: component for components in components_by_taxon.values() for component in components
        },
    }


def build(metric_id: str, components: dict[str, Any]) -> pl.DataFrame:
    metric = components["catalog"].get_metric(metric_id)
    table = MetricStructureTableBuilder(
        components["scope_taxon_category"],
        components["components_by_taxon"],
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
    assert format_metric_location(("busA",)) == "busA"


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
        resolved = components_by_id[comp].resolve_locations(
            ("p_balance_port",), test_3_components["scope_taxon_category"]
        )
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


def test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised(
    test_3_components: dict[str, Any],
) -> None:
    """A port wired to several peers is only ambiguous when more than one of them belongs to the
    view's scope taxonomy category (here "balance").

    In test_3, busA.p_balance_port connects to generator_A1, generator_A2, load_AL,
    link_link_AB, none of which is a "balance" component, so no location can be resolved for
    busA on that port: it must be skipped rather than raise.
    """
    # Arrange
    metric = Metric(
        id="BUS_PEER_TEST",
        terms=[
            Term(
                taxonomy_category="balance",
                output_id="p_balance_port.flow",
                location_ports=("p_balance_port",),
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    builder = MetricStructureTableBuilder(
        test_3_components["scope_taxon_category"],
        test_3_components["components_by_taxon"],
    )

    # Act
    table = builder.build(metric)

    # Assert
    assert table.dataframe.collect().height == 0


def test_compute_component_locations_raises_on_genuine_ambiguity(test_files_root: Path) -> None:
    """Two peers on the same port both belonging to the scope taxonomy category is an actual
    inconsistency and must raise during the up-front location precomputation."""
    # Arrange
    test_3 = test_files_root / "test_3"
    library = load_library(test_3 / "library.yml")
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    components = [Component(component) for component in system.components]
    find_components_taxonomy_categories(components, library.taxonomy_category_by_model)
    component_port_connections = build_component_port_connections(system.connections)
    save_component_port_connections(components, component_port_connections)
    components_by_id = {component.id: component for component in components}
    # Force link_link_AB's p0_port to be wired to both busA and busB (both "balance").
    components_by_id["link_link_AB"].connections["p0_port"] = {"busA", "busB"}

    # Act / Assert
    with pytest.raises(ValueError, match="p0_port"):
        compute_component_locations(components, "balance")


def test_get_location_tuple_of_ports_returns_peer_per_port(test_3_components: dict[str, Any]) -> None:
    """Each port in a location_ports tuple resolves to its connected peer(s)."""
    components_by_id = test_3_components["components_by_id"]
    locations = components_by_id["link_link_AB"].resolve_locations(
        ("p0_port", "p1_port"), test_3_components["scope_taxon_category"]
    )
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
        test_3_components["scope_taxon_category"],
        test_3_components["components_by_taxon"],
    ).build(metric)
    df = table.dataframe.collect()

    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == format_metric_location(
        components_by_id["link_link_AB"].resolve_locations(
            ("p0_port", "p1_port"), test_3_components["scope_taxon_category"]
        )
    )
    assert set(_parse_metric_location(link_rows["metric_location"][0])) == {"busA", "busB"}
    assert set(link_rows["output"].to_list()) == {"p0_port.flow"}


def test_two_ports_resolving_to_same_peer_keep_duplicate_locations_in_single_row(test_files_root: Path) -> None:
    """When two ports resolve to the same peer, the single structure row keeps both locations (busA twice)."""
    # Arrange
    test_3 = test_files_root / "test_3"
    library = load_library(test_3 / "library.yml")
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    view_config = load_view_config(test_3 / "view_config.yml")
    components_by_taxon = build_components_by_taxonomy_category(system, library)
    components_by_id = {
        component.id: component for components in components_by_taxon.values() for component in components
    }

    # Default test_3 wiring uses p0_port -> busA and p1_port -> busB; force both ports to busA here,
    # then recompute locations so the precomputed dictionary reflects the forced wiring.
    components_by_id["link_link_AB"].connections["p0_port"] = {"busA"}
    components_by_id["link_link_AB"].connections["p1_port"] = {"busA"}
    compute_component_locations(list(components_by_id.values()), view_config.scope_taxon_category)
    assert components_by_id["link_link_AB"].resolve_locations(
        ("p0_port", "p1_port"), view_config.scope_taxon_category
    ) == ("busA", "busA")

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
    builder = MetricStructureTableBuilder(view_config.scope_taxon_category, components_by_taxon)

    # Act
    table = builder.build(metric)
    df = table.dataframe.collect()

    # Assert
    link_rows = df.filter(pl.col("component") == "link_link_AB")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == "(busA,busA)"
    assert _parse_metric_location(link_rows["metric_location"][0]) == ["busA", "busA"]


# ---------------------------------------------------------------------------
# Location aggregation fixture
# ---------------------------------------------------------------------------


def _location_aggregation_src(test_files_root: Path) -> Path:
    candidate = test_files_root / "test_location_aggregation"
    if candidate.is_dir():
        return candidate
    alt = test_files_root.parent / "tests" / "test_inputs" / "test_location_aggregation"
    if alt.is_dir():
        return alt
    raise FileNotFoundError(f"test_location_aggregation fixture not found under {test_files_root}")


@pytest.fixture(scope="module")
def loc_agg_components(test_files_root: Path) -> dict[str, Any]:
    fixture = _location_aggregation_src(test_files_root)
    library = load_library(fixture / "library.yml")
    system = load_system(fixture, resolve_libraries(fixture / "library.yml"))
    catalog = load_catalog(fixture / "catalogs" / "catalog.yml")
    taxonomy = load_taxonomy(fixture / "taxonomy.yml")
    view_config = load_view_config(fixture / "view_config.yml")
    components_by_taxon = build_components_by_taxonomy_category(system, library, view_config.scope_taxon_category)
    components_by_id = {
        component.id: component for components in components_by_taxon.values() for component in components
    }
    return {
        "system": system,
        "catalog": catalog,
        "library": library,
        "taxonomy": taxonomy,
        "scope_taxon_category": view_config.scope_taxon_category,
        "components_by_taxon": components_by_taxon,
        "components_by_id": components_by_id,
    }


def _resolve(
    components: dict[str, Any],
    locations: tuple[str, ...],
    location_aggregation: LocationAggregation | None,
) -> tuple[str, ...]:
    components_by_id: dict[str, Component] = components["components_by_id"]
    any_component = next(iter(components_by_id.values()))
    result: tuple[str, ...] = any_component.resolve_location_aggregation(
        locations, location_aggregation, components_by_id
    )
    return result


# ---------------------------------------------------------------------------
# resolve_location_aggregation unit tests
# ---------------------------------------------------------------------------


def test_resolve_single_location_with_property(loc_agg_components: dict[str, Any]) -> None:
    assert _resolve(loc_agg_components, ("area_FR1",), LocationAggregation(key="country")) == ("FR",)


def test_resolve_multiple_locations(loc_agg_components: dict[str, Any]) -> None:
    assert _resolve(loc_agg_components, ("area_FR1", "area_DE"), LocationAggregation(key="country")) == (
        "FR",
        "DE",
    )


def test_resolve_missing_property_keep(loc_agg_components: dict[str, Any]) -> None:
    result = _resolve(loc_agg_components, ("area_orph",), LocationAggregation(key="country", on_missing="keep"))
    assert result == ("<unknown>",)


def test_resolve_missing_property_drop(loc_agg_components: dict[str, Any]) -> None:
    result = _resolve(loc_agg_components, ("area_orph",), LocationAggregation(key="country", on_missing="drop"))
    assert result == ()


def test_resolve_mixed_known_and_unknown_drop(loc_agg_components: dict[str, Any]) -> None:
    result = _resolve(
        loc_agg_components, ("area_FR1", "area_orph"), LocationAggregation(key="country", on_missing="drop")
    )
    assert result == ()


def test_resolve_no_aggregation_passthrough(loc_agg_components: dict[str, Any]) -> None:
    assert _resolve(loc_agg_components, ("area_FR1",), None) == ("area_FR1",)


# ---------------------------------------------------------------------------
# Location aggregation wired through build() — one merged row per component/term
# ---------------------------------------------------------------------------


def test_build_with_country_aggregation_collapses_fr(loc_agg_components: dict[str, Any]) -> None:
    """gen_FR1 and gen_FR2 both resolve to 'FR' via the country property."""
    metric = loc_agg_components["catalog"].get_metric("PRODUCTION")
    table = MetricStructureTableBuilder(
        loc_agg_components["scope_taxon_category"],
        loc_agg_components["components_by_taxon"],
        location_aggregation=LocationAggregation(key="country"),
    ).build(metric)
    df = table.dataframe.collect()
    fr_rows = df.filter(pl.col("metric_location") == "FR")
    assert set(fr_rows["component"].to_list()) == {"gen_FR1", "gen_FR2"}
    assert df.filter(pl.col("metric_location").is_in(["area_FR1", "area_FR2"])).is_empty()


def test_build_with_drop_excludes_orphan(loc_agg_components: dict[str, Any]) -> None:
    """gen_orph has no country property; on_missing=drop excludes it."""
    metric = loc_agg_components["catalog"].get_metric("PRODUCTION")
    table = MetricStructureTableBuilder(
        loc_agg_components["scope_taxon_category"],
        loc_agg_components["components_by_taxon"],
        location_aggregation=LocationAggregation(key="country", on_missing="drop"),
    ).build(metric)
    df = table.dataframe.collect()
    assert "gen_orph" not in df["component"].to_list()
    assert "<unknown>" not in df["metric_location"].to_list()


def test_build_multiport_location_ports_with_aggregation(loc_agg_components: dict[str, Any]) -> None:
    """A term with location_ports=(p0_port, p1_port) on link_FRDE produces one row with '(FR,DE)'."""
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
    table = MetricStructureTableBuilder(
        loc_agg_components["scope_taxon_category"],
        loc_agg_components["components_by_taxon"],
        location_aggregation=LocationAggregation(key="country"),
    ).build(metric)
    df = table.dataframe.collect()
    link_rows = df.filter(pl.col("component") == "link_FRDE")
    assert len(link_rows) == 1
    assert link_rows["metric_location"][0] == "(FR,DE)"
    assert "area_FR1" not in link_rows["metric_location"][0]
    assert "area_DE" not in link_rows["metric_location"][0]
