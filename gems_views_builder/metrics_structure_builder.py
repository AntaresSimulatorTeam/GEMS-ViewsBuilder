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
from gems_views_builder.input.view_config import LocationAggregation
from gems_views_builder.metric_structure_table import MetricStructureTable


class MetricStructureTableBuilder:
    """Build metric structure rows without loading unrelated datasets."""

    def __init__(
        self,
        scope_taxon_category: str,
        components_by_taxon: dict[str, list[Component]],  # taxonomy category -> components
        location_aggregation: LocationAggregation | None = None,
    ) -> None:
        self.scope_taxon_category = scope_taxon_category
        self.components_by_taxon = components_by_taxon  # this is mainly for operating
        self.location_aggregation = location_aggregation

    def _resolve_location_aggregation(self, locations: list[str]) -> list[str]:
        """Filter and relabel raw location component IDs using the configured property key.

        Each location is resolved independently. Locations where the property is
        undeclared are replaced with ``<unknown>`` (on_missing='keep') or
        excluded (on_missing='drop'). When no location_aggregation is configured
        the list is returned unchanged.
        """
        location = self.location_aggregation
        if location is None:
            return locations
        result: list[str] = []
        for loc in locations:
            val = self.system.get_component(loc).properties.get(location.key)
            if val is not None:
                result.append(val)
            elif location.on_missing == "keep":
                result.append("<unknown>")
            elif location.on_missing == "drop":
                return []

        return result

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in metric.terms:
            logging.debug(
                f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )

            for c in self.components_by_taxon[term.taxonomy_category]:
                if c.match(metric.filter) and c.is_located_at(term.location_ports, self.scope_taxon_category):
                    rows.append(
                        {
                            "metric_id": metric.id,
                            "component": c.id,
                            "metric_location": c.formatted_locations(term.location_ports, self.scope_taxon_category),
                            "breakdown_properties": c.format_breakdown_properties(metric.breakdown),
                            "output": term.output_id,
                            "weight_output_id": 1,
                        }
                    )
        return MetricStructureTable(rows, metric.id)
