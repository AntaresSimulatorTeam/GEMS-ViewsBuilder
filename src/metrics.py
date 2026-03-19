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

"""ViewConfig: in memory representation of a view_config.yml file."""

from collections import defaultdict
from enum import Enum
from pathlib import Path

import polars as pl
import yaml
from pydantic import Field

from src.base_model import ViewBuilderBasedModel
from src.calendar import Calendar
from src.catalog import Catalog, Metric
from src.model_library import ModelLibrary
from src.system import InputSystem
from src.taxonomy import Taxonomy


class TimeAggregation(Enum):
    HOURS = "hours"


class Scope(ViewBuilderBasedModel):
    taxonomy_category: str | None = Field(None, alias="taxonomy-category")
    calendar: str | None = None


class Aggregation(ViewBuilderBasedModel):
    time: TimeAggregation | None = None


class CatalogRef(ViewBuilderBasedModel):
    id: str


class MetricRef(ViewBuilderBasedModel):
    id: str


class ViewData(ViewBuilderBasedModel):
    id: str
    scope: list[Scope]
    aggregation: list[Aggregation]
    catalog: list[CatalogRef]
    metrics: list[MetricRef]


class ViewConfig:
    """
    In memory representation of the view_config.yml file.
    """

    def __init__(self, config_file_path: Path) -> None:
        parsed = self._load_view_file(config_file_path)
        self.input_data_path = config_file_path.parent
        self.id = parsed.id
        self.location_taxonomy_category: str = next(
            item.taxonomy_category for item in parsed.scope if item.taxonomy_category
        )
        self.calendar_id: str = next(item.calendar for item in parsed.scope if item.calendar)
        self.catalog_ids: list[str] = [c.id for c in parsed.catalog]
        self.time_aggregation: TimeAggregation | None = parsed.aggregation[0].time if parsed.aggregation else None
        # Public API: list of (catalog_id, metric_id) pairs
        self.metrics: list[tuple[str, str]] = self._extract_metric_pairs(parsed.metrics)
        # Internal helper: grouped by catalog
        self.metrics_by_catalog: dict[str, list[str]] = self._group_metrics_by_catalog(self.metrics)

    def _extract_metric_pairs(self, metrics: list[MetricRef]) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for metric in metrics:
            catalog_id, metric_id = metric.id.split(".", 1)
            pairs.append((catalog_id, metric_id))
        return pairs

    def _group_metrics_by_catalog(self, metrics: list[tuple[str, str]]) -> dict[str, list[str]]:
        metrics_for_catalog: dict[str, list[str]] = defaultdict(list)
        for catalog_id, metric_id in metrics:
            metrics_for_catalog[catalog_id].append(metric_id)
        return metrics_for_catalog

    def _load_view_file(self, view_file_path: Path) -> ViewData:
        with open(view_file_path) as f:
            raw = yaml.safe_load(f)
        return ViewData.model_validate(raw["view"])

    def _load_current_catalog(self, catalog_id: str) -> Catalog:
        """
        This method prevents us from having all catalogs in memory at once
        Just load when that is needed
        """
        if not (self.input_data_path / "catalogs" / f"{catalog_id}.yml").exists():
            raise FileNotFoundError(f"Catalog file {self.input_data_path / 'catalogs' / f'{catalog_id}.yml'} not found")
        return Catalog(self.input_data_path / "catalogs" / f"{catalog_id}.yml")

    def _load_calendar(self) -> Calendar:
        """
        This method prevents calendars in memory
        Just load when that is needed,(e.g. when we're filtering simulation table)
        """
        if not (self.input_data_path / f"{self.calendar_id}.csv").exists():
            raise FileNotFoundError(f"Calendar file {self.input_data_path / f'{self.calendar_id}.csv'} not found")
        return Calendar(self.input_data_path / f"{self.calendar_id}.csv")


class MetricStructureBuilder:
    """InputSystem from GemsPy. LIST_OF_COMPONENTS_IN_TAXONOMY_CATEGORY, LOCATING_FUNCTION, build_tables (spec 2.1)."""

    def __init__(
        self,
        system: InputSystem,
        catalog: Catalog,
        metric: Metric,
        taxonomy: Taxonomy,
        model_library: ModelLibrary,
        path_to_output_table: Path,
    ) -> None:
        self.system = system
        self.catalog = catalog
        self.metric = metric
        self.taxonomy = taxonomy
        self.model_library = model_library
        self.path_to_output_table = path_to_output_table
        self.current_schema: pl.DataFrame = pl.DataFrame(
            schema={
                "metric_id": pl.Utf8,
                "component_id": pl.Utf8,
                "metric_location": pl.Utf8,
                "breakdown_properties": pl.Utf8,
                "output_id": pl.Utf8,
                "weight_output_id": pl.Int64,  # # What will be value range here, probably we could use Int8 to save memory?
            }
        )

    def build_table(self) -> None:
        """
        # Idea is to write table at the provided output path
        # then when we perform SQL operation we could do lazy loading and avoid loading in memory
        """
        self.path_to_output_table.parent.mkdir(parents=True, exist_ok=True)
        schema = self.current_schema.schema
        # Create the file with header once; then always append without header.
        if (not self.path_to_output_table.exists()) or self.path_to_output_table.stat().st_size == 0:
            pl.DataFrame(schema=schema).write_csv(self.path_to_output_table)

        def append_row_polars(row: dict[str, object]) -> None:
            row_df = pl.DataFrame([row], schema=schema)
            with self.path_to_output_table.open("a") as f:
                row_df.write_csv(f, include_header=False)

        for term in self.metric.terms:
            # # Pick components whih belongs to the taxonomy category, from model library
            components_in_taxonomy_category = self.model_library.get_components_in_taxonomy_category(
                term.taxonomy_category
            )  # # O(1) access insted of O(n) from pseudo code
            for component_id in components_in_taxonomy_category:
                # # Here will be applied filter with respect to properties of the component
                # # Breakdown properties will be applied here

                # # locating function
                metric_location = self.system.locating_function(component_id, term.location_ports)
                # # append to the output csv on disk (polars write)
                append_row_polars(
                    {
                        "metric_id": self.metric.id,
                        "component_id": component_id,
                        "metric_location": metric_location,  # # We should force users to have names for example fr_battery, then we could parse easy component id
                        "breakdown_properties": "",
                        "output_id": term.output_id,
                        "weight_output_id": 1,  # # Default value
                    }
                )
