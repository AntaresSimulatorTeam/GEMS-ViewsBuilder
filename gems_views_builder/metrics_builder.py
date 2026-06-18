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
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from gems.study import Component  # type: ignore[import-untyped]

from gems_views_builder.input.catalog import Metric, PropertySchema
from gems_views_builder.input.library import Library
from gems_views_builder.input.system import System
from gems_views_builder.writer import Writer

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
    component_properties: dict[str, str], breakdown: list[PropertySchema] | None
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
        system: System,
        metric: Metric,
        model_library: Library,
    ) -> None:
        self.system = system
        self.metric = metric
        self.model_library = model_library

    def build(self) -> MetricStructureTable:
        logging.debug(f"[{self.metric.id}] Building metric structure table ({len(self.metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            logging.debug(
                f"[{self.metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )
            model_ids = self.model_library.get_components_in_taxonomy_category(term.taxonomy_category)
            logging.debug(
                f"[{self.metric.id}] Found {len(model_ids)} model(s) in taxonomy category {term.taxonomy_category!r}"
            )
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                component_ids = self.system.get_instances_by_model(qualified_ref)
                logging.debug(
                    f"[{self.metric.id}] Model {qualified_ref!r} resolves to {len(component_ids)} component instance(s)"
                )
                for component_id in component_ids:
                    component = self.system.get_component(component_id)

                    # # Decide does the component matches the filter, if yes they will contribute to the metric
                    if _check_filter_matches(component, self.metric.filter):
                        metric_location = _format_metric_location(
                            self.system.get_location(component_id, term.location_ports)
                        )
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
                        logging.debug(
                            f"[{self.metric.id}] Component {component_id!r} did not match metric filter and was skipped"
                        )

        if not rows:
            logging.info(f"[{self.metric.id}] No matching components found — metric structure table is empty")
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        logging.info(f"[{self.metric.id}] Metric structure table built with {len(rows)} row(s)")
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))


@dataclass
class MetricStructure:
    """On-disk metric structure table, ready for lazy scanning and cleanup."""

    file: Path
    dataframe: pl.LazyFrame

    def cleanup(self) -> None:
        logging.info(f"Cleaning metric structure {self.file}")
        self.file.unlink(missing_ok=True)


def build_metric_structure(
    system: System,
    metric: Metric,
    library: Library,
    writer: Writer,
) -> MetricStructure:
    """Build the metric structure table, persist it via writer, and return a MetricStructure."""
    table = MetricStructureBuilder(system, metric, library).build()
    path = writer.write_metric_structure_table(table.dataframe, metric.id)
    return MetricStructure(path, pl.scan_parquet(path))
