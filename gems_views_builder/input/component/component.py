import logging
from dataclasses import dataclass, field
from typing import cast

from gems.study import Component as GemsPyComponent  # type: ignore

from gems_views_builder.input.catalog import PropertySchema
from gems_views_builder.input.component.connection import ConnectionThroughPort
from gems_views_builder.input.view_config import LocationAggregation


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
    # Connections holding the peer components connected on each port
    connections: list[ConnectionThroughPort] = field(default_factory=list)
    # (port_id, taxonomy_category) -> unique peer component id located on that port for that
    # taxonomy category. Populated by ``supply_components_with_locations``. Absence of a key means no
    # peer on that port belongs to that taxonomy category (no location can be determined there).
    scope_locations: dict[tuple[str, str], str] = field(default_factory=dict)

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

    def is_located_at(self, location_port: str | None, taxonomy_category: str) -> bool:
        """Whether ``location_port`` has a resolved location for ``taxonomy_category``.

        ``location_port`` of ``None`` means the component is its own location: always true.
        """
        if location_port is None:
            return True
        located = (location_port, taxonomy_category) in self.scope_locations
        if not located:
            logging.debug(f"Component {self.id!r} has no resolved location for taxonomy category {taxonomy_category!r}")
        return located

    def resolve_location(self, location_port: str | None, taxonomy_category: str) -> str:
        """Return the resolved location for ``location_port``, previously checked via ``is_located_at``."""
        if location_port is None:
            return self.id
        return self.scope_locations[(location_port, taxonomy_category)]

    def aggregated_locations(
        self,
        location_port: str | None,
        taxonomy_category: str,
        location_aggregation: LocationAggregation | None,
        components_by_id: dict[str, "Component"],
    ) -> tuple[str, ...]:
        location_components_ids = (self.resolve_location(location_port, taxonomy_category),)
        return self.resolve_location_aggregation(location_components_ids, location_aggregation, components_by_id)

    def resolve_location_aggregation(
        self,
        location_components_ids: tuple[str, ...],
        location_aggregation: LocationAggregation | None,
        components_by_id: dict[str, "Component"],
    ) -> tuple[str, ...]:
        if location_aggregation is None:
            return location_components_ids

        result: list[str] = []
        for component_id in location_components_ids:
            property_value = components_by_id[component_id].properties.get(location_aggregation.key)
            if property_value is not None:
                result.append(property_value)
            elif location_aggregation.on_missing == "keep":
                result.append("<unknown>")
            elif location_aggregation.on_missing == "drop":
                return ()

        return tuple(result)

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
