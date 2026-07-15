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

from gems_views_builder.input.catalog import Metric, PropertySchema
from gems_views_builder.input.component import Component
from gems_views_builder.metric_structure_table import MetricStructureTable


def _check_filter_matches(component: Component, filter: PropertySchema | None) -> bool:
    if filter is None:
        return True
    return bool(component.properties.get(filter.key) == filter.value)


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
        location_taxonomy_category: str,
        components_by_taxon: dict[str, list[Component]],  # taxonomy category -> components
    ) -> None:
        self.location_taxonomy_category = location_taxonomy_category
        self.components_by_taxon = components_by_taxon  # this is mainly for operating

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
                    rows.append(
                        {
                            "metric_id": metric.id,
                            "component": c.id,
                            "metric_location": c.resolve_location(term.location_port, self.location_taxonomy_category),
                            "breakdown_properties": c.format_breakdown_properties(metric.breakdown),
                            "output": term.output_id,
                            "weight_output_id": 1,
                        }
                    )
        return MetricStructureTable(rows, metric.id)
