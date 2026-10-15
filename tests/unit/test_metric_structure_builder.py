# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import polars as pl
import pytest

from gems_views_builder.input.component import ConnectionsThroughPort, supply_components_with_locations
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from tests.common import make_component, make_metric, make_view_config


def test_port_whose_peers_are_outside_the_location_category_is_skipped() -> None:
    """Peers that are not in the view's location category do not locate the component, so the row is skipped."""
    bus = make_component(taxonomy_category="balance", component_id="bus")
    generator = make_component(taxonomy_category="production", component_id="generator")
    load = make_component(taxonomy_category="consumption", component_id="load")
    bus.connections = ConnectionsThroughPort(port_components={"p_port": [generator, load]})
    metric = make_metric("BUS", "balance", "p_port", "flow")

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
    metric = make_metric("AMBIGUITY_TEST", "cat", "p0_port", "flow")

    with pytest.raises(ValueError, match="p0_port"):
        supply_components_with_locations(components_by_taxon, [metric], "cat")


def test_location_returns_peer_component() -> None:
    link = make_component(taxonomy_category="link", component_id="link")
    bus = make_component(taxonomy_category="balance", component_id="busA")
    link.connections = ConnectionsThroughPort(port_components={"p0_port": [bus]})
    metric = make_metric("FLOW", "link", "p0_port", "flow")

    supply_components_with_locations({"link": [link]}, [metric], "balance")

    assert link.location("p0_port", "balance").id == "busA"


def test_none_location_port_resolves_to_the_component_itself() -> None:
    """A term with location_port=None means the component is its own location.

    Self-location is only valid when the term taxonomy category matches the view's
    location taxonomy category.
    """
    bus = make_component(taxonomy_category="balance", component_id="busA")
    metric = make_metric("SELF_LOCATED", "balance", output_id="flow")
    components_by_taxon = {"balance": [bus]}
    supply_components_with_locations(components_by_taxon, [metric], "balance")

    table = MetricStructureTableBuilder(make_view_config(), components_by_taxon).build(metric)
    df = table.dataframe.collect()

    assert df.height == 1
    bus_rows = df.filter(pl.col("component") == "busA")
    assert bus_rows["metric_location"][0] == "busA"
