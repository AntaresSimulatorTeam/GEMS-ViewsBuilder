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

from gems_views_builder.catalog import Catalog, Metric
from gems_views_builder.common import logger
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


class MetricStructureBuilder:
    """Build metric structure rows without loading unrelated datasets."""

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
        logger.info(f"[{self.metric.id}] Building metric structure table ({len(self.metric.terms)} term(s))")
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            logger.info(
                f"[{self.metric.id}] Processing term for taxonomy category {term.taxonomy_category!r} "
                f"and output {term.output_id!r}"
            )
            model_ids = self.model_library.get_components_in_taxonomy_category(term.taxonomy_category)
            logger.info(
                f"[{self.metric.id}] Found {len(model_ids)} model(s) in taxonomy category {term.taxonomy_category!r}"
            )
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                component_ids = self.system.get_instances_by_model(qualified_ref)
                logger.info(
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
            logger.info(f"[{self.metric.id}] No matching components found — metric structure table is empty")
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        logger.info(f"[{self.metric.id}] Metric structure table built with {len(rows)} row(s)")
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))
