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

import polars as pl
from gems.study import Component  # type: ignore

from gems_views_builder.common import METRIC_STRUCTURE_TABLE_SCHEMA
from gems_views_builder.input.catalog import Metric, PropertySchema
from gems_views_builder.input.library import Library
from gems_views_builder.input.system import System
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
        system: System,
        model_library: Library,
    ) -> None:
        self.system = system
        self.model_library = model_library

    def build(self, metric: Metric) -> MetricStructureTable:
        logging.debug(f"[{metric.id}] Building metric structure table ({len(metric.terms)} term(s))")
        rows_data: list[dict[str, object]] = []
        for term in metric.terms:
            logging.debug(
                f"[{metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )
            model_ids = self.model_library.get_models_in_taxonomy_category(term.taxonomy_category)
            logging.debug(
                f"[{metric.id}] Found {len(model_ids)} model(s) in taxonomy category {term.taxonomy_category!r}"
            )
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                component_ids = self.system.get_instances_by_model(qualified_ref)
                logging.debug(
                    f"[{metric.id}] Model {qualified_ref!r} resolves to {len(component_ids)} component instance(s)"
                )
                for component_id in component_ids:
                    component = self.system.get_component(component_id)

                    # # Decide does the component matches the filter, if yes they will contribute to the metric
                    if _check_filter_matches(component, metric.filter):
                        metric_location = _format_metric_location(
                            self.system.get_location(component_id, term.location_ports)
                        )
                        breakdown_properties = _format_breakdown_properties(component.properties, metric.breakdown)
                        rows_data.append(
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

        rows = pl.DataFrame(rows_data, schema=METRIC_STRUCTURE_TABLE_SCHEMA)
        return MetricStructureTable(rows, metric.id)
