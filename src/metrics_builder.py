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

from src.catalog import Catalog, Metric
from src.library import ModelLibrary
from src.system import InputSystem
from src.taxonomy import Taxonomy

_METRIC_STRUCTURE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.Utf8,
        "component_id": pl.Utf8,
        "metric_location": pl.Utf8,
        "breakdown_properties": pl.Utf8,
        "output_id": pl.Utf8,
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
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            # # Pick components whih belongs to the taxonomy category, from model library
            components_in_taxonomy_category = self.model_library.get_components_in_taxonomy_category(
                term.taxonomy_category
            )  # # O(1) access insted of O(n) from pseudo code
            for component_id in components_in_taxonomy_category:
                # # Here will be applied filter with respect to properties of the component
                # # Breakdown properties will be applied here

                # # locating function
                metric_location = self.system.get_location(component_id, term.location_ports)
                loc_str = metric_location if isinstance(metric_location, str) else "|".join(metric_location)
                rows.append(
                    {
                        "metric_id": self.metric.id,
                        "component_id": component_id,
                        "metric_location": loc_str,
                        "breakdown_properties": "",
                        "output_id": term.output_id,
                        "weight_output_id": 1,  # # Default value for now
                    }
                )
        if not rows:
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))
