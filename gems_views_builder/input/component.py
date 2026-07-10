import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, cast

from gems.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.catalog import PropertySchema


@dataclass
class Component:
    """
    Each component hold raw data from real component used for building additional fields
    Taxonomy category
    Connections to other components
    """

    raw_component: GemsPyComponent
    taxonomy_category: str | None = None
    # port_id -> set of peer component ids connected on that port
    connections: dict[str, set[str]] = field(default_factory=dict)
    # (port_id, taxonomy_category) -> unique peer component id located on that port for that
    # taxonomy category. Populated by ``compute_component_locations``. Absence of a key means no
    # peer on that port belongs to that taxonomy category (no location can be determined there).
    locations: dict[tuple[str, str], str] = field(default_factory=dict)

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

    def is_located_at(self, location_ports: tuple[str, ...] | None, taxonomy_category: str) -> bool:
        """Whether every port in ``location_ports`` has a resolved location for ``taxonomy_category``.

        ``location_ports`` of ``None`` means the component is its own location: always true.
        """
        if location_ports is None:
            return True
        located = all((port, taxonomy_category) in self.locations for port in location_ports)
        if not located:
            logging.debug(f"Component {self.id!r} has no resolved location for taxonomy category {taxonomy_category!r}")
        return located

    def resolve_locations(self, location_ports: tuple[str, ...] | None, taxonomy_category: str) -> tuple[str, ...]:
        """Return the resolved location(s) for ``location_ports``, previously checked via ``is_located_at``."""
        if location_ports is None:
            return (self.id,)
        return tuple(self.locations[(port, taxonomy_category)] for port in location_ports)

    def formatted_locations(self, location_ports: tuple[str, ...] | None, taxonomy_category: str) -> str:
        return format_metric_location(self.resolve_locations(location_ports, taxonomy_category))

    def format_breakdown_properties(self, breakdown: list[PropertySchema] | None) -> str:
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

    def match(self, filter: PropertySchema | None) -> bool:
        if filter is None:
            return True
        matched = bool(self.properties.get(filter.key) == filter.value)
        if not matched:
            logging.debug(f"Component {self.id!r} did not match metric filter and was skipped")
        return matched


def find_components_taxonomy_categories(
    components: list[Component], taxonomy_category_by_model: dict[str, str]
) -> None:
    for component in components:
        component.taxonomy_category = taxonomy_category_by_model[component.model_id]


def group_components_by_taxon(components: list[Component]) -> dict[str, list[Component]]:
    """Group components by taxonomy category. Requires ``find_components_taxonomy_categories`` to have run first."""
    components_by_taxon: dict[str, list[Component]] = defaultdict(list)
    for component in components:
        components_by_taxon[cast(str, component.taxonomy_category)].append(component)
    return components_by_taxon


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


def compute_component_locations(components: list[Component], taxonomy_category: str) -> None:
    """Precompute, for every component's port, the unique peer belonging to taxonomy_category.

    Requires find_components_taxonomy_categories and save_component_port_connections to have
    already run. For each (component, port), among the peers connected on that port, only those
    belonging to ``taxonomy_category`` are considered:
    - zero matching peers: no location is stored for that port (components referencing it are
      later skipped when building the metric structure table);
    - exactly one: it is stored as the resolved location;
    - more than one: a genuine inconsistency, raised immediately rather than later during table
      building.
    """
    logging.info(f"Resolving component locations for taxonomy category {taxonomy_category!r}")
    components_by_id = {component.id: component for component in components}
    for component in components:
        for port_id, peer_ids in component.connections.items():
            matching_peers = [
                peer_id for peer_id in peer_ids if components_by_id[peer_id].taxonomy_category == taxonomy_category
            ]
            if len(matching_peers) > 1:
                raise ValueError(
                    f"Component {component.id!r} port {port_id!r} has {len(matching_peers)} peers "
                    f"belonging to taxonomy category {taxonomy_category!r}: {tuple(sorted(matching_peers))!r}, "
                    f"expected at most one"
                )
            if len(matching_peers) == 1:
                component.locations[(port_id, taxonomy_category)] = matching_peers[0]
    logging.info(f"Component locations resolved for taxonomy category {taxonomy_category!r}")


def format_metric_location(locations: tuple[str, ...]) -> str:
    if len(locations) == 1:
        return locations[0]
    return "(" + ",".join(locations) + ")"
