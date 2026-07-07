import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, cast

from gems.study import Component as GemsComponent  # type: ignore

from gems_views_builder.input.catalog import PropertySchema


@dataclass
class Component:
    """
    Each component hold raw data from real component used for building additional fields
    Taxonomy category
    Connections to other components
    """

    raw_component: GemsComponent
    taxonomy_category: str | None = None
    # port_id -> set of peer component ids connected on that port
    connections: dict[str, set[str]] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return str(self.raw_component.id)

    @property
    def model_id(self) -> str:
        # resolved model id is qualified, e.g. "basic_lib.area" -> "area"
        return str(self.raw_component.model.id).rsplit(".", 1)[-1]

    @property
    def properties(self) -> dict[str, str]:
        return cast(dict[str, str], self.raw_component.properties)

    def set_taxonomy_category(self, taxonomy_category: str) -> None:
        self.taxonomy_category = taxonomy_category

    def get_location(self, location_ports: str | tuple[str, ...] | None) -> str | tuple[str, ...]:
        """Resolve the component's location for the given location port(s).

        - None: the component is its own location.
        - single port: the unique peer connected on that port.
        - tuple of ports: one unique peer per port, in order.
        """
        if location_ports is None:
            return self.id
        if isinstance(location_ports, str):
            return self._resolve_unique_location(location_ports)
        return tuple(self._resolve_unique_location(port) for port in location_ports)

    def _resolve_unique_location(self, location_port: str) -> str:
        """Return the UNIQUE peer connected on ``location_port`` (O(1) lookup)."""
        peers = self.connections.get(location_port, set())
        if len(peers) != 1:
            raise ValueError(
                f"Expected exactly one peer component for component {self.id!r} "
                f"on port {location_port!r}, but found {len(peers)}: {tuple(peers)!r}"
            )
        return next(iter(peers))

    def _format_breakdown_properties(self, breakdown: list[PropertySchema] | None) -> str:
        if not breakdown:
            return "{}"
        pairs: list[str] = []
        for prop in breakdown:
            key = prop.key
            if key not in self.properties:
                pairs.append(f"({key},None)")
            else:
                pairs.append(f"({key},{self.properties[key]})")
        return "{" + ",".join(pairs) + "}"

    def check_component_filter_matches(self, filter: PropertySchema | None) -> bool:
        if filter is None:
            return True
        return bool(self.properties.get(filter.key) == filter.value)


def find_components_taxonomy_categories(
    components: list[Component], taxonomy_category_by_model: dict[str, str]
) -> None:
    for component in components:
        component.taxonomy_category = taxonomy_category_by_model[component.model_id]


def group_components_by_taxonomy_category(components: list[Component]) -> dict[str, dict[str, Component]]:
    """Group components by taxonomy category. Requires ``find_components_taxonomy_categories`` to have run first."""
    components_by_taxonomy_category: dict[str, dict[str, Component]] = defaultdict(dict)
    for component in components:
        components_by_taxonomy_category[cast(str, component.taxonomy_category)][component.id] = component
    return components_by_taxonomy_category


def save_component_port_connections(
    components: list[Component], component_port_connections: dict[str, dict[str, set[str]]]
) -> None:
    for component in components:
        if component.id in component_port_connections:
            component.connections = component_port_connections[component.id]


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
