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
        components_by_taxono: dict[str, list[Component]],  # taxonomy category -> components
    ) -> None:
        self.location_taxonomy_category = location_taxonomy_category
        self.components_by_taxono = components_by_taxono  # this is mainly for operating

    def _location_components_match_taxonomy_category(self, location_components: tuple[str, ...]) -> None:
        # # This will break computation so we need to perform it before running pipeline
        if self.location_taxonomy_category is None:
            return

        component_ids = {c.id for c in self.components_by_taxono[self.location_taxonomy_category]}
        for location_component_id in location_components:
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

            for c in self.components_by_taxono[term.taxonomy_category]:
                if c.match(metric.filter):
                    locations = c._get_locations(location_ports=term.location_ports)
                    self._location_components_match_taxonomy_category(locations)
                    rows.append(
                        {
                            "metric_id": metric.id,
                            "component": c.id,
                            "metric_location": format_metric_location(locations),
                            "breakdown_properties": c.format_breakdown_properties(metric.breakdown),
                            "output": term.output_id,
                            "weight_output_id": 1,
                        }
                    )
                else:
                    logging.debug(f"[{metric.id}] Component {c.id!r} did not match metric filter and was skipped")
        return MetricStructureTable(rows, metric.id)


def format_metric_location(locations: tuple[str, ...]) -> str:
    if len(locations) == 1:
        return locations[0]
    return "(" + ",".join(locations) + ")"
