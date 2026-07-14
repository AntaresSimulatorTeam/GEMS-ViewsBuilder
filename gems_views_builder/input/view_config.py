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

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.input.catalog import Catalog, Metric


class TimeAggregation(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class LocationCategory(ViewBuilderBasedModel):
    taxonomy_category: str


class Calendar(ViewBuilderBasedModel):
    id: str


class Scope(ViewBuilderBasedModel):
    location: LocationCategory | None = None
    calendar: Calendar | None = None


class Aggregation(ViewBuilderBasedModel):
    time: TimeAggregation | None = None


class CatalogId(ViewBuilderBasedModel):
    id: str


class TaxonomyId(ViewBuilderBasedModel):
    id: str


class MetricId(ViewBuilderBasedModel):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str
    taxonomy: list[TaxonomyId] = Field(min_length=1, max_length=1)
    scope: list[Scope] = Field(min_length=2, max_length=2)
    aggregation: list[Aggregation]
    catalog: list[CatalogId] = Field(min_length=1)  # We need minimum one catalog and metric
    metrics: list[MetricId] = Field(min_length=1)  # in fact if we don't have it GVB process is useless


@dataclass
class ViewConfig:
    id: str
    input_data_path: Path
    calendar_id: str
    location_taxonomy_category: str
    taxonomy_id: str
    catalog_ids: set[str] = field(default_factory=set)
    time_aggregation: TimeAggregation | None = None
    metric_ids: list[str] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)

    def fetch_metrics(self, catalogs: list[Catalog]) -> None:
        metric_ids_by_catalog = self._group_metrics_by_catalog()
        for catalog in catalogs:
            if catalog.id not in metric_ids_by_catalog:
                raise ValueError(
                    f"Catalog {catalog.id!r} has no metrics referenced in the view config. "
                    f"Metric refs must use the catalog id from the catalog file "
                    f"(expected prefixes: {sorted(metric_ids_by_catalog)})"
                )
            for metric_id in metric_ids_by_catalog[catalog.id]:
                self.metrics.append(catalog.get_metric(metric_id))

    def _group_metrics_by_catalog(self) -> dict[str, set[str]]:
        logging.debug(f"Grouping {len(self.metric_ids)} metric id(s) by catalog")
        metric_ids_by_catalog: dict[str, set[str]] = defaultdict(set)
        for metric_ref in self.metric_ids:
            if "." not in metric_ref or metric_ref.startswith(".") or metric_ref.endswith("."):
                raise ValueError(
                    f"Invalid metric id '{metric_ref}'. "
                    f"Expected format '<catalog_id>.<metric_id>' for catalog {self.catalog_ids}"
                )
            catalog_id, metric_id = metric_ref.split(".", 1)
            if catalog_id not in self.catalog_ids:
                raise ValueError(f"Catalog {catalog_id!r} not found in view config")
            metric_ids_by_catalog[catalog_id].add(metric_id)
            logging.debug(f"Mapped metric {metric_id!r} to catalog {catalog_id!r}")
        return metric_ids_by_catalog


def load_view_config(config_file_path: Path) -> ViewConfig:
    from gems_views_builder.validation.raw_view_config_validator import RawViewConfigValidator

    logging.info(f"Loading view config from {config_file_path}")
    raw_view_config = load_raw_view_config_file(config_file_path)
    RawViewConfigValidator(raw_view_config).validate()

    location_taxonomy_category = next(
        item.location.taxonomy_category for item in raw_view_config.scope if item.location is not None
    )
    calendar_id = next(item.calendar.id for item in raw_view_config.scope if item.calendar is not None)

    view_config = ViewConfig(
        id=raw_view_config.id,
        input_data_path=config_file_path.parent,
        calendar_id=calendar_id,
        location_taxonomy_category=location_taxonomy_category,
        catalog_ids={c.id for c in raw_view_config.catalog},
        time_aggregation=raw_view_config.aggregation[0].time if raw_view_config.aggregation else None,
        metric_ids=[metric.id for metric in raw_view_config.metrics],
        taxonomy_id=raw_view_config.taxonomy[0].id,
    )
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"catalogs={len(view_config.catalog_ids)}, metrics={len(view_config.metric_ids)}"
    )
    return view_config


def load_raw_view_config_file(view_file_path: Path) -> RawViewConfig:
    logging.info(f"Parsing view config YAML from {view_file_path}")
    with open(view_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "view" not in raw:
        raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
    logging.info(f"View config YAML parsed successfully from {view_file_path}")
    return RawViewConfig.model_validate(raw["view"])
