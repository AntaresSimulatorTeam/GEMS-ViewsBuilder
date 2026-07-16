import logging
from collections import defaultdict
from typing import Any, cast

from gems.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.component.component import Component
from gems_views_builder.input.component.connection import Connection


def create_components(gemspy_components: list[GemsPyComponent]) -> list[Component]:
    return [Component(component) for component in gemspy_components]


def supply_components_with_taxonomy_categories(
    components: list[Component], taxonomy_category_by_model: dict[str, str]
) -> None:
    for component in components:
        component.taxonomy_category = taxonomy_category_by_model[component.model_id]


def group_components_by_taxon(components: list[Component]) -> dict[str, list[Component]]:
    """Group components by taxonomy category. Requires ``supply_components_with_taxonomy_categories`` first."""
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
            component.connections = [
                Connection(port=port_id, components=[components_by_id[peer_id] for peer_id in peer_ids])
                for port_id, peer_ids in component_port_connections[component.id].items()
            ]


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


def supply_components_with_locations(components: list[Component], taxonomy_category: str) -> None:
    """Precompute, for every component's port, the unique peer belonging to taxonomy_category.

    Requires supply_components_with_taxonomy_categories and supply_components_with_port_connections to have
    already run. For each (component, port), among the peers connected on that port, only those
    belonging to ``taxonomy_category`` are considered:
    - zero matching peers: no location is stored for that port (components referencing it are
      later skipped when building the metric structure table);
    - exactly one: it is stored as the resolved location;
    - more than one: a genuine inconsistency, raised immediately rather than later during table
      building.
    """
    logging.info(f"Resolving component locations for taxonomy category {taxonomy_category!r}")
    for c in components:
        for connection in c.connections:
            connected_components = [
                peer for peer in connection.components if peer.taxonomy_category == taxonomy_category
            ]
            if len(connected_components) > 1:
                raise ValueError(
                    f"Component {c.id!r} port {connection.port!r} has {len(connected_components)} peers "
                    f"belonging to taxonomy category {taxonomy_category!r}: "
                    f"{tuple(sorted(peer.id for peer in connected_components))!r}, expected at most one"
                )
            if len(connected_components) == 1:
                c.locations[(connection.port, taxonomy_category)] = connected_components[0].id
    logging.info(f"Component locations resolved for taxonomy category {taxonomy_category!r}")
