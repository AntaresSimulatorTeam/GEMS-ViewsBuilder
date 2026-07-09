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

from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.component import Component
from gems_views_builder.metric_structure_table import MetricStructureTable


class MetricStructureTableBuilder:
    """Build metric structure rows without loading unrelated datasets."""

    def __init__(
        self,
        location_taxonomy_category: str | None,
        components_by_taxonomy_category: dict[
            str, list[Component]
        ],  # taxonomy category -> components
    ) -> None:
        self.location_taxonomy_category = location_taxonomy_category
        self.components_by_taxonomy_category = components_by_taxonomy_category  # this is mainly for operating

    def _location_components_match_taxonomy_category(self, location_components: str | tuple[str, ...]) -> None:
        if self.location_taxonomy_category is None:
            return

        location_component_ids = (location_components,) if isinstance(location_components, str) else location_components
        component_ids = {c.id for c in self.components_by_taxonomy_category[self.location_taxonomy_category]}
        for location_component_id in location_component_ids:
            if location_component_id not in component_ids:
                raise ValueError(
                    f"Location component {location_component_id!r} must belong to taxonomy category {self.location_taxonomy_category!r}"
                )

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in metric.terms:
            logging.debug(
                f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )

            for c in self.components_by_taxonomy_category[term.taxonomy_category]:
                if c.match(metric.filter):
                    location = c.get_location(location_ports=term.location_ports)
                    self._location_components_match_taxonomy_category(location)
                    rows.append(
                        {
                            "metric_id": metric.id,
                            "component": c.id,
                            "metric_location": format_metric_location(location),
                            "breakdown_properties": c.format_breakdown_properties(metric.breakdown),
                            "output": term.output_id,
                            "weight_output_id": 1,
                        }
                    )
                else:
                    logging.debug(f"[{metric.id}] Component {c.id!r} did not match metric filter and was skipped")
        return MetricStructureTable(rows, metric.id)


def format_metric_location(locations: str | tuple[str, ...]) -> str:
    if isinstance(locations, str):
        return locations
    return "(" + ",".join(locations) + ")"
