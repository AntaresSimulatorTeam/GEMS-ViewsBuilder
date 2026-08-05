# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

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
    ConnectionsThroughPort,
    build_component_port_connections,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.library import resolve_libraries
from gems_views_builder.input.system import load_system
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def build_components_by_taxonomy_category(
    system: Any,
    library: Any,
    metrics: list[Metric] | None = None,
    location_taxonomy_category: str | None = None,
) -> dict[str, list[Component]]:
    components = [Component(component) for component in system.components]
    supply_components_with_taxonomy_categories(components, library.taxonomy_category_by_model)
    components_by_taxon = group_components_by_taxon(components)
    component_port_connections = build_component_port_connections(system.connections)
    supply_components_with_port_connections(components, component_port_connections)
    if metrics is not None:
        if location_taxonomy_category is None:
            raise ValueError("location_taxonomy_category is required when metrics are provided")
        supply_components_with_locations(components_by_taxon, metrics, location_taxonomy_category)
    return components_by_taxon


@pytest.fixture(scope="module")
def test_3_components(test_files_root: Path) -> dict[str, Any]:
    test_3 = test_files_root / "test_3"
    system = load_system(test_3, resolve_libraries(test_3 / "library.yml"))
    taxonomy = load_taxonomy(test_3 / "taxonomy.yml")
    library = load_library(test_3 / "library.yml")
    catalog = load_catalog(test_3 / "catalogs" / "catalog.yml")
    view_config = load_view_config(test_3 / "view_config.yml")
    components_by_taxon = build_components_by_taxonomy_category(
        system, library, list(catalog.metrics.values()), view_config.location_taxonomy_category
    )
    return {
        "system": system,
        "taxonomy": taxonomy,
        "library": library,
        "catalog": catalog,
        "view_config": view_config,
        "location_taxonomy_category": view_config.location_taxonomy_category,
        "components_by_taxon": components_by_taxon,
        "components_by_id": {
            component.id: component for components in components_by_taxon.values() for component in components
        },
    }


def build(metric_id: str, components: dict[str, Any]) -> pl.DataFrame:
    metric = components["catalog"].get_metric(metric_id)
    table = MetricStructureTableBuilder(
        components["view_config"],
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
        resolved = components_by_id[comp].resolve_location(
            "p_balance_port", test_3_components["location_taxonomy_category"], []
        )
        assert comp_rows["metric_location"].to_list() == resolved


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
                location_port="p_balance_port",
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    builder = MetricStructureTableBuilder(
        test_3_components["view_config"],
        test_3_components["components_by_taxon"],
    )

    # Act
    table = builder.build(metric)

    # Assert
    assert table.dataframe.collect().height == 0


def test_supply_components_with_locations_raises_on_genuine_ambiguity() -> None:
    """Two peers on the same port both belonging to the term's taxonomy category is an actual
    inconsistency and must raise during the up-front location precomputation."""
    # Arrange
    owner = make_component({})
    peer_1 = make_component({})
    peer_2 = make_component({})
    owner.taxonomy_category = "cat"
    peer_1.taxonomy_category = "cat"
    peer_2.taxonomy_category = "cat"
    owner.connections = ConnectionsThroughPort(port_components={"p0_port": [peer_1, peer_2]})
    components_by_taxon = {"cat": [owner]}
    metric = Metric(
        id="AMBIGUITY_TEST",
        terms=[Term(taxonomy_category="cat", output_id="o", location_port="p0_port")],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )

    # Act / Assert
    with pytest.raises(ValueError, match="p0_port"):
        supply_components_with_locations(components_by_taxon, [metric], "cat")


def test_resolve_location_returns_peer(test_3_components: dict[str, Any]) -> None:
    """A location_port resolves to its connected peer."""
    # Arrange
    components_by_id = test_3_components["components_by_id"]

    # Act
    location = components_by_id["link_link_AB"].resolve_location(
        "p0_port", test_3_components["location_taxonomy_category"], []
    )

    # Assert
    assert location == ["busA"]


def test_none_location_port_resolves_to_the_component_itself(test_3_components: dict[str, Any]) -> None:
    """A term with location_port=None means the component is its own location.

    Self-location is only valid when the term taxonomy category matches the view's
    location taxonomy category (here ``balance``).
    """
    # Arrange
    location_taxonomy_category = test_3_components["location_taxonomy_category"]
    metric = Metric(
        id="SELF_LOCATED_TEST",
        terms=[
            Term(
                taxonomy_category=location_taxonomy_category,
                output_id="p_balance_port.flow",
                location_port=None,
            )
        ],
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
    )
    supply_components_with_locations(test_3_components["components_by_taxon"], [metric], location_taxonomy_category)
    builder = MetricStructureTableBuilder(
        test_3_components["view_config"],
        test_3_components["components_by_taxon"],
    )

    # Act
    table = builder.build(metric)
    df = table.dataframe.collect()

    # Assert
    bus_rows = df.filter(pl.col("component") == "busA")
    assert len(bus_rows) == 1
    assert bus_rows["metric_location"][0] == "busA"
