import logging
from dataclasses import dataclass, field
from typing import cast

from gems.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.catalog import PropertySchema


def format_metric_location(locations: tuple[str, ...]) -> str:
    if len(locations) == 1:
        return locations[0]
    return "(" + ",".join(locations) + ")"


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
    # taxonomy category. Populated by ``supply_components_with_locations``. Absence of a key means no
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
