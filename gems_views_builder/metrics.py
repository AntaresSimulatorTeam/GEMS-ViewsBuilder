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

"""ViewConfig models and lazy loaders for view_config.yml."""

from collections import defaultdict
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.calendar import Calendar, load_calendar
from gems_views_builder.catalog import Catalog, load_catalog


class TimeAggregation(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


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
    Parsed view configuration with on-demand loading of referenced files.
    """

    def __init__(self, config_file_path: Path) -> None:
        """
        Cheap constructor: keep only the path.

        Use `ViewConfig.load(...)` (or `load_into_self()`) to perform YAML I/O and validation.
        """
        self.file = config_file_path
        self.input_data_path = config_file_path.parent
        self.id = ""
        self.location_taxonomy_category: str | None = None
        self.calendar_id: str | None = None
        self.catalog_ids: list[str] = []
        self.time_aggregation: TimeAggregation | None = None
        self.catalog_to_metrics: dict[str, list[str]] = {}

    @classmethod
    def load(cls, config_file_path: Path) -> "ViewConfig":
        return cls(config_file_path).load_into_self()

    def load_into_self(self) -> "ViewConfig":
        parsed = self._load_view_file(self.file)
        self.id = parsed.id
        self.location_taxonomy_category = next(
            (item.taxonomy_category for item in parsed.scope if item.taxonomy_category),
            None,
        )
        if self.location_taxonomy_category is None:
            raise ValueError(
                f"view_config.yml '{parsed.id}': no 'taxonomy-category' found in scope. "
                f"At least one scope entry must define a taxonomy-category"
            )
        self.calendar_id = next((item.calendar for item in parsed.scope if item.calendar), None)
        self.catalog_ids = [c.id for c in parsed.catalog]
        self.time_aggregation = parsed.aggregation[0].time if parsed.aggregation else None
        # Internal helper: grouped by catalog
        self.catalog_to_metrics = self._group_metrics_by_catalog(parsed.metrics)
        return self

    def _group_metrics_by_catalog(self, metrics: list[MetricRef]) -> dict[str, list[str]]:
        catalog_to_metrics: dict[str, list[str]] = defaultdict(list)
        for metric in metrics:
            if "." not in metric.id or metric.id.startswith(".") or metric.id.endswith("."):
                raise ValueError(
                    f"view_config.yml '{self.id}': invalid metric id '{metric.id}'. "
                    "Expected format '<catalog_id>.<metric_id>'"
                )
            catalog_id, metric_id = metric.id.split(".", 1)
            catalog_to_metrics[catalog_id].append(metric_id)
        return catalog_to_metrics

    def _load_view_file(self, view_file_path: Path) -> ViewData:
        with open(view_file_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if "view" not in raw:
            raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
        return ViewData.model_validate(raw["view"])

    def load_catalog(self, catalog_id: str) -> Catalog:
        """
        Load only the requested catalog when needed instead of preloading all catalogs.
        """
        if not (self.input_data_path / "catalogs" / f"{catalog_id}.yml").exists():
            raise FileNotFoundError(f"Catalog file {self.input_data_path / 'catalogs' / f'{catalog_id}.yml'} not found")
        return load_catalog(self.input_data_path / "catalogs" / f"{catalog_id}.yml")

    def load_calendar(self) -> Calendar:
        """
        Load only the referenced calendar when needed.
        """
        calendar_file = self.input_data_path / f"{self.calendar_id}.csv"
        if not calendar_file.exists():
            raise FileNotFoundError(f"Calendar file {calendar_file} not found")
        return load_calendar(calendar_file)
