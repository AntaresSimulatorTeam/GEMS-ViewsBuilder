from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any
from gems.study import Component as GemsComponent

from gems_views_builder.input.catalog import PropertySchema
import logging

@dataclass
class Component:
    """
    Each component hold raw data from real component used for building additional fields
    Taxonomy category
    Connections to other components
    """

    raw_component: GemsComponent
    taxonomy_category: str | None = None
    connections: set[tuple[str, str]] = field(default_factory=set)

    @property
    def id(self) -> str:
        return str(self.raw_component.id)

    @property
    def model_id(self) -> str:
        # resolved model id is qualified, e.g. "basic_lib.area" -> "area"
        return str(self.raw_component.model.id).rsplit(".", 1)[-1]

    @property
    def properties(self) -> dict[str, str]:
        return self.raw_component.properties

    def set_taxonomy_category(self, taxonomy_category: str) -> None:
        self.taxonomy_category = taxonomy_category


def find_components_taxonomy_categories(
    components: list[Component], taxonomy_category_by_model: dict[str, str]
) -> None:
    for component in components:
        component.taxonomy_category = taxonomy_category_by_model[component.model_id]

def group_components_by_taxonomy_category(components: list[Component]) -> dict[str, list[Component]]:
    components_by_taxonomy_category = defaultdict(list)
    for component in components:
        components_by_taxonomy_category[component.taxonomy_category].append(component)
    return components_by_taxonomy_category

def check_component_filter_matches(component: Component, filter: PropertySchema | None) -> bool:
    if filter is None:
        return True
    return bool(component.properties.get(filter.key) == filter.value)


def save_component_port_connections(components: list[Component], component_port_connections: dict[str, set[tuple[str, str]]]) -> None:
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

def build_component_port_connections(connections: list[Any]) -> dict[str, set[tuple[str, str]]]:
    """
    One time build which will be used to save information inside component object
    """
    logging.info("Building component-port connection index")
    component_port_connections: dict[str, set[tuple[str, str]]] = defaultdict(set)
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

        component_port_connections[c1].add((p1,c2))
        component_port_connections[c2].add((p2,c1))

    logging.info(f"Built component-port connection index with {len(component_port_connections)} entry(ies)")
    return component_port_connections