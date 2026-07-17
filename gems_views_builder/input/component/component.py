import logging
from dataclasses import dataclass, field
from typing import cast

from gems.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.catalog import PropertySchema
from gems_views_builder.input.component.connection import ConnectionThroughPort


@dataclass
class Component:
    """
    Each component hold raw data from real component used for building additional fields
    Taxonomy category
    Connections to other components
    """

    raw_component: GemsPyComponent
    taxonomy_category: str | None = None
    # Connections holding the peer components connected on each port
    connections: ConnectionThroughPort = field(default_factory=ConnectionThroughPort)
    # (location_port, taxonomy_category) -> resolved location component id.
    # Populated by ``supply_components_with_locations``:
    # - location_port set: unique peer on that port for the peer's taxonomy category;
    # - location_port None: the component itself for the view's location taxonomy category.
    # Absence of a key means no location can be determined for that (port, category).
    locations: dict[tuple[str | None, str], str] = field(default_factory=dict)

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

    def is_located_at(self, location_port: str | None, location_taxonomy_category: str) -> bool:
        """Whether a location was precomputed for ``(location_port, location_taxonomy_category)``."""
        located = (location_port, location_taxonomy_category) in self.locations
        if not located:
            logging.debug(
                f"Component {self.id!r} has no resolved location for "
                f"port {location_port!r} and taxonomy category {location_taxonomy_category!r}"
            )
        return located

    def resolve_location(self, location_port: str | None, location_taxonomy_category: str) -> str:
        """Return the resolved location, previously checked via ``is_located_at``."""
        return self.locations[(location_port, location_taxonomy_category)]

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
