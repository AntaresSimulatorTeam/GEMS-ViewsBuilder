# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.component import Component
from gems_views_builder.metric_structure_table import MetricStructureTable


@dataclass
class MetricStructureTableBuilder:
    location_taxonomy_category: str
    components_by_taxon: dict[str, list[Component]]  # taxonomy category -> components
    extra_locations: list[str]  # empty list means no extra locations

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in metric.terms:
            logging.debug(
                f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )

            for c in self.components_by_taxon[term.taxonomy_category]:
                if c.match(metric.filter) and c.is_located_at(term.location_port, self.location_taxonomy_category):
                    locations = c.resolve_location(
                        term.location_port, self.location_taxonomy_category, self.extra_locations
                    )
                    breakdown_properties = c.format_breakdown_properties(metric.breakdown)
                    for location in locations:
                        rows.append(
                            {
                                "metric_id": metric.id,
                                "component": c.id,
                                "metric_location": location,
                                "breakdown_properties": breakdown_properties,
                                "output": term.output_id,
                                "weight_output_id": 1,
                            }
                        )
        return MetricStructureTable(rows, metric.id)
