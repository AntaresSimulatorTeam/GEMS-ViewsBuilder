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

from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.library import Library
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
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


class MetricStructureBuilder:
    """Build metric structure rows without loading unrelated datasets."""

    def __init__(
        self,
        system: System,
        metric: Metric,
        taxonomy: Taxonomy,
        model_library: Library,
    ) -> None:
        self.system = system
        self.metric = metric
        self.taxonomy = taxonomy
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
                    # # locating function
                    metric_location = self.system.get_location(component_id, term.location_ports)
                    loc_str = metric_location if isinstance(metric_location, str) else "|".join(metric_location)
                    rows.append(
                        {
                            "metric_id": self.metric.id,
                            "component": component_id,
                            "metric_location": loc_str,
                            "breakdown_properties": "",
                            "output": term.output_id,
                            "weight_output_id": 1,
                        }
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
    taxonomy: Taxonomy,
    library: Library,
    writer: Writer,
) -> MetricStructure:
    """Build the metric structure table, persist it via writer, and return a MetricStructure."""
    table = MetricStructureBuilder(system, metric, taxonomy, library).build()
    path = writer.write_metric_structure_table(table.dataframe, metric.id)
    return MetricStructure(path, pl.scan_parquet(path))
