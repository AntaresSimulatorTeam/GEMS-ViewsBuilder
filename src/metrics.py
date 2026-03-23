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

from src.base_model import ViewBuilderBasedModel
from src.calendar import Calendar, load_calendar
from src.catalog import Catalog, load_catalog


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
    Parsed view configuration with on-demand loading of referenced files.
    """

    def __init__(self, config_file_path: Path) -> None:
        parsed = self._load_view_file(config_file_path)
        self.input_data_path = config_file_path.parent
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
            if "." not in metric.id or metric.id.startswith(".") or metric.id.endswith("."):
                raise ValueError(
                    f"view_config.yml '{self.id}': invalid metric id '{metric.id}'. "
                    "Expected format '<catalog_id>.<metric_id>'"
                )
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
