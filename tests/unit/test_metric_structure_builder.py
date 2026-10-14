# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

import polars as pl
import pytest

from gems_views_builder import AggregOperatorType, Metric, Term
from gems_views_builder.input.component import (
    Component,
    ConnectionsThroughPort,
    supply_components_with_locations,
)
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def make_component(
    taxonomy_category: str, properties: dict[str, str] | None = None, component_id: str = "fake"
) -> Component:
    return Component(
        SimpleNamespace(id=component_id, model=SimpleNamespace(id="lib.model"), properties=properties or {}),
        taxonomy_category=taxonomy_category,
    )


def make_metric(metric_id: str, taxonomy_category: str, location_port: str | None) -> Metric:
    return Metric(
        id=metric_id,
        terms=[Term(taxonomy_category=taxonomy_category, output_id="flow", location_port=location_port)],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
    )


def make_view_config() -> ViewConfig:
    return ViewConfig(
        id="view",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
    )


def test_port_whose_peers_are_outside_the_location_category_is_skipped() -> None:
    """Peers that are not in the view's location category do not locate the component, so the row is skipped."""
    bus = make_component(taxonomy_category="balance", component_id="bus")
    generator = make_component(taxonomy_category="production", component_id="generator")
    load = make_component(taxonomy_category="consumption", component_id="load")
    bus.connections = ConnectionsThroughPort(port_components={"p_port": [generator, load]})
    metric = make_metric("BUS", "balance", "p_port")

    table = MetricStructureTableBuilder(make_view_config(), {"balance": [bus]}).build(metric)

    assert table.dataframe.collect().height == 0


def test_supply_components_with_locations_raises_on_genuine_ambiguity() -> None:
    """Two peers on the same port both belonging to the term's taxonomy category is an actual
    inconsistency and must raise during the up-front location precomputation."""
    owner = make_component(taxonomy_category="cat")
    peer_1 = make_component(taxonomy_category="cat")
    peer_2 = make_component(taxonomy_category="cat")
    owner.connections = ConnectionsThroughPort(port_components={"p0_port": [peer_1, peer_2]})
    components_by_taxon = {"cat": [owner]}
    metric = make_metric("AMBIGUITY_TEST", "cat", "p0_port")

    with pytest.raises(ValueError, match="p0_port"):
        supply_components_with_locations(components_by_taxon, [metric], "cat")


def test_location_returns_peer_component() -> None:
    link = make_component(taxonomy_category="link", component_id="link")
    bus = make_component(taxonomy_category="balance", component_id="busA")
    link.connections = ConnectionsThroughPort(port_components={"p0_port": [bus]})
    metric = make_metric("FLOW", "link", "p0_port")

    supply_components_with_locations({"link": [link]}, [metric], "balance")

    assert link.location("p0_port", "balance").id == "busA"


def test_none_location_port_resolves_to_the_component_itself() -> None:
    """A term with location_port=None means the component is its own location.

    Self-location is only valid when the term taxonomy category matches the view's
    location taxonomy category.
    """
    bus = make_component(taxonomy_category="balance", component_id="busA")
    metric = make_metric("SELF_LOCATED", "balance", None)
    components_by_taxon = {"balance": [bus]}
    supply_components_with_locations(components_by_taxon, [metric], "balance")

    table = MetricStructureTableBuilder(make_view_config(), components_by_taxon).build(metric)
    df = table.dataframe.collect()

    assert df.height == 1
    bus_rows = df.filter(pl.col("component") == "busA")
    assert bus_rows["metric_location"][0] == "busA"
