# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast

from gems_craft.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.component.component import Component
from gems_views_builder.input.component.connection import ConnectionsThroughPort
from gems_views_builder.input.library import associate_models_with_a_taxon

if TYPE_CHECKING:
    from gems_views_builder.input.raw_input_data import RawInputData


def create_components(gemspy_components: list[GemsPyComponent]) -> list[Component]:
    return [Component(component) for component in gemspy_components]


def enrich_components(components: list[Component], raw_input_data: RawInputData) -> None:
    """Attach taxonomy categories and port connections to components."""
    supply_components_with_taxon(components, associate_models_with_a_taxon(raw_input_data.libraries))
    component_port_connections = build_component_port_connections(raw_input_data.system.connections)
    supply_components_with_port_connections(components, component_port_connections)


def supply_components_with_taxon(components: list[Component], taxonomy_category_by_model: dict[str, str]) -> None:
    for component in components:
        component.taxonomy_category = taxonomy_category_by_model[component.model_id]


def group_components_by_taxon(components: list[Component]) -> dict[str, list[Component]]:
    """Group components by taxonomy category. Requires ``supply_components_with_taxon`` first."""
    components_by_taxon: dict[str, list[Component]] = defaultdict(list)
    for component in components:
        components_by_taxon[cast(str, component.taxonomy_category)].append(component)
    return components_by_taxon


def supply_components_with_port_connections(
    components: list[Component], component_port_connections: dict[str, dict[str, set[str]]]
) -> None:
    components_by_id = {component.id: component for component in components}
    for component in components:
        if component.id in component_port_connections:
            component.connections = ConnectionsThroughPort(
                port_components={
                    port_id: [components_by_id[peer_id] for peer_id in peer_ids]
                    for port_id, peer_ids in component_port_connections[component.id].items()
                }
            )


def endpoint(conn: Any, idx: int) -> tuple[str, str] | None:
    """
    Return (component_id, port_id) for side `idx` in {1,2}, handling both:
    - parsed YAML connections (string fields component1/port1/component2/port2)
    - resolved connections (PortRef objects in port1/port2)
    """
    comp = getattr(conn, f"component{idx}", None)
    port = getattr(conn, f"port{idx}", None)

    # Resolved `PortsConnection`: port is a PortRef with {component, port_id}
    if comp is None and port is not None and not isinstance(port, str):
        comp_obj = getattr(port, "component", None)
        comp = getattr(comp_obj, "id", None)
        port = getattr(port, "port_id", None)

    if not (isinstance(comp, str) and comp and isinstance(port, str) and port):
        return None
    return comp, port


def build_component_port_connections(connections: list[Any]) -> dict[str, dict[str, set[str]]]:
    """
    One time build which will be used to save information inside component object.

    Shape: component_id -> {port_id -> {peer_component_ids}}, so each component can
    resolve a location by port in O(1).
    """
    logging.info("Building component-port connection index")
    component_port_connections: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for connection in connections:
        e1 = endpoint(connection, 1)
        e2 = endpoint(connection, 2)
        if e1 is None or e2 is None:
            continue

        (c1, p1), (c2, p2) = e1, e2

        # Some datasets omit port2, callers treated that as "same as port1".
        if not p2:
            p2 = p1

        if c1 == c2:
            continue

        component_port_connections[c1][p1].add(c2)
        component_port_connections[c2][p2].add(c1)

    logging.info(f"Built component-port connection index with {len(component_port_connections)} entry(ies)")
    return component_port_connections


def supply_components_with_locations(
    components_by_taxon: dict[str, list[Component]],
    metrics: list[Metric],
    location_taxonomy_category: str,
) -> None:
    """Precompute each component's metric locations from catalog terms.

    Must run after:
    - ``supply_components_with_taxon``
    - ``supply_components_with_port_connections``

    For each metric term and each component in that term's taxonomy category,
    resolve ``(location_port, location_taxonomy_category)`` once per component
    (later metrics that reuse the same term shape are skipped):

    - ``location_port is None``: the component is its own location; store
      ``(None, location_taxonomy_category) -> component``.
    - ``location_port`` is set: require exactly one peer on that port belonging to
      ``location_taxonomy_category``, then store that peer component; more than one raises.

    Later read via ``Component.is_located_at`` / ``Component.location``, which look up
    ``(location_port, location_taxonomy_category)`` in ``Component.locations``.
    """
    for metric in metrics:
        for term in metric.terms:
            for c in components_by_taxon[term.taxonomy_category]:
                location_key = (term.location_port, location_taxonomy_category)
                if location_key in c.locations:
                    continue
                if term.location_port is None:
                    if term.taxonomy_category != location_taxonomy_category:
                        raise ValueError(
                            f"Component {c.id!r} has taxonomy category {c.taxonomy_category!r}, "
                            f"expected {location_taxonomy_category!r}"
                        )
                    c.locations[location_key] = c
                else:
                    supply_component_with_location(c, term.location_port, location_taxonomy_category)


def supply_component_with_location(component: Component, location_port: str, location_taxonomy_category: str) -> None:
    peers = component.connections.get_components(location_port)
    if len(peers) != 1:
        raise ValueError(f"Component {component.id!r} port {location_port} has {len(peers)} peers, expected 1")
    if peers[0].taxonomy_category != location_taxonomy_category:
        raise ValueError(
            f"Component {component.id!r} port {location_port} has peer {peers[0].id!r} with taxonomy category {peers[0].taxonomy_category!r}, expected {location_taxonomy_category!r}"
        )
    component.locations[(location_port, location_taxonomy_category)] = peers[0]
