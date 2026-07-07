# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging

from gems.study import Component  # type: ignore

from gems_views_builder.input.catalog import Metric, PropertySchema
from gems_views_builder.input.library import Library
from gems_views_builder.input.system import System
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.input.component import check_component_filter_matches





def _format_breakdown_properties(component_properties: dict[str, str], breakdown: list[PropertySchema] | None) -> str:
    if not breakdown:
        return "{}"
    pairs: list[str] = []
    for prop in breakdown:
        key = prop.key
        if key not in component_properties:
            pairs.append(f"({key},None)")
        else:
            pairs.append(f"({key},{component_properties[key]})")
    return "{" + ",".join(pairs) + "}"


def _format_metric_location(locations: str | tuple[str, ...]) -> str:
    if isinstance(locations, str):
        return locations
    return "(" + ",".join(locations) + ")"


class MetricStructureTableBuilder:
    """Build metric structure rows without loading unrelated datasets."""

    def __init__(
        self,
        system: System,
        model_library: Library,
        location_taxonomy_category: str | None,
        components_by_taxonomy_category: dict[str, list[Component]],
    ) -> None:
        self.system = system
        self.model_library = model_library
        self.location_taxonomy_category = location_taxonomy_category
        self.components_by_taxonomy_category = components_by_taxonomy_category # this is mainly for operating
    def _location_component_matches_taxonomy_category(self, location_component_id: str) -> bool:
        """Return True when the located component's model belongs to the view location taxonomy category."""
        if self.location_taxonomy_category is None:
            return True
        location_component = self.system.get_component(location_component_id)
        model_id = self.system.get_model_id_from_component(location_component)
        return self.model_library.get_taxonomy_category(model_id) == self.location_taxonomy_category

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in metric.terms:
            logging.debug(
                f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )

            for component in self.components_by_taxonomy_category[term.taxonomy_category]:
                if check_component_filter_matches(component, metric.filter):
                    # # Now in components we have connections 
                    # # Now we need here to get location from component
                    # # component.get_location(term.location_ports) and component needs to answer on this in O(1)
                    pass
                else:
                    logging.debug(
                            f"[{metric.id}] Component {component_id!r} did not match metric filter and was skipped"
                        )
                
                # # Here I have regular component

            # # Component needs to know which taxonomy category it belongs to
            model_ids = self.model_library.get_models_in_taxonomy_category(term.taxonomy_category)
            logging.debug(
                f"[{metric.id}] Found {len(model_ids)} model(s) in taxonomy category {term.taxonomy_category!r}"
            )

            for model_id in model_ids:
                # # This needs to be transfered to component responsibility
                qualified_ref = f"{self.model_library.id}.{model_id}"
                component_ids = self.system.get_instances_by_model(qualified_ref)
                logging.debug(
                    f"[{metric.id}] Model {qualified_ref!r} resolves to {len(component_ids)} component instance(s)"
                )
                for component_id in component_ids:
                    component = self.system.get_component(component_id)

                    # # Tgis information needs to be held in component
                    if check_component_filter_matches(component, metric.filter):
                        # # This needs to be hered because it's processed bt term
                        raw_location = self.system.get_location(component_id, term.location_ports)
                        raw_locations = [raw_location] if isinstance(raw_location, str) else list(raw_location)
                        for loc_id in raw_locations:
                            # # This needs to be moved inside component responsibility
                            assert self._location_component_matches_taxonomy_category(loc_id), (
                                f"Metric {metric.id!r} term {term.output_id!r}: location component {loc_id!r} "
                                f"must belong to taxonomy category {self.location_taxonomy_category!r}"
                            )
                        metric_location = (
                            raw_locations[0]
                            if len(raw_locations) == 1
                            else _format_metric_location(tuple(raw_locations))
                        )
                        breakdown_properties = _format_breakdown_properties(component.properties, metric.breakdown)
                        rows.append(
                            {
                                "metric_id": metric.id,
                                "component": component_id,
                                "metric_location": metric_location,
                                "breakdown_properties": breakdown_properties,
                                "output": term.output_id,
                                "weight_output_id": 1,
                            }
                        )
                    else:
                        logging.debug(
                            f"[{metric.id}] Component {component_id!r} did not match metric filter and was skipped"
                        )

        return MetricStructureTable(rows, metric.id)
