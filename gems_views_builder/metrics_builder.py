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

from gems_views_builder.catalog import Catalog, Metric, PropertySchema
from gems_views_builder.common import logger
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics import LocationAggregation
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


def _check_filter_matches(component: Component, filter: PropertySchema | None) -> bool:
    if filter is None:
        return True
    return bool(component.properties.get(filter.key) == filter.value)


def _format_breakdown_properties(
    component_properties: dict[str, str], breakdown: tuple[PropertySchema, ...] | None
) -> str:
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
    locs = (locations,) if isinstance(locations, str) else locations
    if not locs:
        return "{}"
    return "{" + ",".join(locs) + "}"


class MetricStructureBuilder:
    def __init__(
        self,
        system: InputSystem,
        catalog: Catalog,
        metric: Metric,
        taxonomy: Taxonomy,
        model_library: ModelLibrary,
        location_aggregation: LocationAggregation | None = None,
    ) -> None:
        self.system = system
        self.catalog = catalog
        self.metric = metric
        self.taxonomy = taxonomy
        self.model_library = model_library
        self.location_aggregation = location_aggregation

    def _resolve_location_aggregation(self, locations: list[str]) -> list[str]:
        """Filter and relabel raw location component IDs using the configured property key.

        Each location is resolved independently. Locations where the property is
        undeclared are replaced with ``<unknown>`` (on_missing='keep') or
        excluded (on_missing='drop'). When no location_aggregation is configured
        the list is returned unchanged.
        """
        cfg = self.location_aggregation
        if cfg is None:
            return locations
        result: list[str] = []
        for loc in locations:
            val = self.system.get_component(loc).properties.get(cfg.key)
            if val is not None:
                result.append(val)
            elif cfg.on_missing == "keep":
                result.append("<unknown>")
            # else on_missing == "drop": skip this location
        return result

    def build(self) -> MetricStructureTable:
        logger.debug(f"[{self.metric.id}] Building metric structure table ({len(self.metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            logger.debug(
                f"[{self.metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )
            model_ids = self.model_library.get_components_in_taxonomy_category(term.taxonomy_category)
            logger.debug(
                f"[{self.metric.id}] Found {len(model_ids)} model(s) in taxonomy category {term.taxonomy_category!r}"
            )
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                component_ids = self.system.get_instances_by_model(qualified_ref)
                logger.debug(
                    f"[{self.metric.id}] Model {qualified_ref!r} resolves to {len(component_ids)} component instance(s)"
                )
                for component_id in component_ids:
                    component = self.system.get_component(component_id)

                    # # Decide does the component matches the filter, if yes they will contribute to the metric
                    if _check_filter_matches(component, self.metric.filter):
                        raw_location = self.system.get_location(component_id, term.location_ports)
                        raw_locations = [raw_location] if isinstance(raw_location, str) else list(raw_location)
                        resolved_locations = self._resolve_location_aggregation(raw_locations)
                        if not resolved_locations:
                            logger.debug(
                                f"[{self.metric.id}] Component {component_id!r} has no locations after "
                                "aggregation and was skipped"
                            )
                            continue
                        metric_location = _format_metric_location(tuple(resolved_locations))
                        breakdown_properties = _format_breakdown_properties(component.properties, self.metric.breakdown)
                        rows.append(
                            {
                                "metric_id": self.metric.id,
                                "component": component_id,
                                "metric_location": metric_location,
                                "breakdown_properties": breakdown_properties,
                                "output": term.output_id,
                                "weight_output_id": 1,
                            }
                        )
                    else:
                        logger.debug(
                            f"[{self.metric.id}] Component {component_id!r} did not match metric filter and was skipped"
                        )

        if not rows:
            logger.info(f"[{self.metric.id}] No matching components found — metric structure table is empty")
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        logger.info(f"[{self.metric.id}] Metric structure table built with {len(rows)} row(s)")
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))
