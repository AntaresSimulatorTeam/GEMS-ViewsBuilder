# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input.catalog import Metric, Term
from gems_views_builder.input.component import Component
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_structure_table import MetricStructureTable


@dataclass
class MetricStructureTableBuilder:
    view_config: ViewConfig
    components_by_taxon: dict[str, list[Component]]  # taxonomy category -> components

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in metric.terms:
            log_term_processing(metric, term)
            for c in self.components_by_taxon[term.taxonomy_category]:
                if c.match(metric.filter) and c.is_located_at(
                    term.location_port, self.view_config.location_taxonomy_category
                ):
                    location_component = c.location(term.location_port, self.view_config.location_taxonomy_category)
                    # for each aggregation perform separated extra location matching
                    locations = [location_component.id] + location_component.match_extra_locations(
                        self.view_config.extra_locations
                    )
                    breakdown_prop = c.format_breakdown_properties(metric.breakdown)
                    rows.extend(make_row(metric, term, c, location, breakdown_prop) for location in locations)
        return MetricStructureTable(rows, metric.id)


def log_term_processing(metric: Metric, term: Term) -> None:
    logging.debug(
        f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} and output {term.output_id!r}"
    )


def make_row(metric: Metric, term: Term, c: Component, location: str, breakdown_prop: str) -> dict[str, object]:
    return {
        "metric_id": metric.id,
        "component": c.id,
        "metric_location": location,
        "breakdown_properties": breakdown_prop,
        "output": term.output_id,
        "weight_output_id": 1,
    }
