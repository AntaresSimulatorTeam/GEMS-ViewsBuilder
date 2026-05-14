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

from dataclasses import dataclass

import polars as pl
from gems.study import Component  # type: ignore[import-untyped]

from gems_views_builder.catalog import Catalog, Metric, PropertyKey, PropertyTuple
from gems_views_builder.library import ModelLibrary
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import Taxonomy

_METRIC_STRUCTURE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.Utf8,
        "component": pl.Utf8,
        "metric_location": pl.Utf8,
        "breakdown_properties": pl.Utf8,
        "output": pl.Utf8,
        "weight_output_id": pl.Int64,  # # What will be value range here, probably we could use Int8 to save memory?
    }
)


@dataclass(frozen=True)
class MetricStructureTable:
    """Metric structure table produced from catalog metric terms (spec 2.1)."""

    dataframe: pl.DataFrame


def _check_filter_matches(component: Component, filter: tuple[PropertyTuple, ...] | None) -> bool:
    if filter is None:
        return True
    return all(component.properties.get(c.key) == c.value for c in filter)


def _format_breakdown_properties(
    component_properties: dict[str, str], breakdown_keys: tuple[PropertyKey, ...] | None
) -> str:
    if not breakdown_keys:
        return "{}"
    pairs: list[str] = []
    for breakdown_key in breakdown_keys:
        key = breakdown_key.key
        if key not in component_properties:
            return "{}"
        pairs.append(f"({key},{component_properties[key]})")
    return "{" + ",".join(pairs) + "}"


class MetricStructureBuilder:
    def __init__(
        self,
        system: InputSystem,
        catalog: Catalog,
        metric: Metric,
        taxonomy: Taxonomy,
        model_library: ModelLibrary,
    ) -> None:
        self.system = system
        self.catalog = catalog
        self.metric = metric
        self.taxonomy = taxonomy
        self.model_library = model_library

    def build(self) -> MetricStructureTable:
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            model_ids = self.model_library.get_components_in_taxonomy_category(term.taxonomy_category)
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                for component_id in self.system.get_instances_by_model(qualified_ref):
                    component = self.system.get_component(component_id)

                    # # Decide does the component matches the filter, if yes they will contribute to the metric
                    if _check_filter_matches(component, self.metric.filter):
                        metric_location = self.system.get_location(component_id, term.location_ports)
                        loc_str = metric_location if isinstance(metric_location, str) else "|".join(metric_location)

                        breakdown_properties = _format_breakdown_properties(component.properties, self.metric.breakdown)
                        rows.append(
                            {
                                "metric_id": self.metric.id,
                                "component": component_id,
                                "metric_location": loc_str,
                                "breakdown_properties": breakdown_properties,
                                "output": term.output_id,
                                "weight_output_id": 1,
                            }
                        )

        if not rows:
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))
