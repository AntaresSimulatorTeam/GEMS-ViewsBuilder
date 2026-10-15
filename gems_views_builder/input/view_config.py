# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""ViewConfig models and lazy loaders for view_config.yml."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.input.catalog import Catalog, Metric


class ExtraLocation(ViewBuilderBasedModel):
    id: str


class TimeGranularity(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Location(ViewBuilderBasedModel):
    taxonomy_category: str


class Scope(ViewBuilderBasedModel):
    location: Location
    calendar: str
    extra_locations: list[ExtraLocation] | None = Field(default=None, min_length=0)


class AggregationPattern(ViewBuilderBasedModel):
    id: str
    time_granularity: TimeGranularity
    scenario: bool
    spatial_filter: list[str] | None = Field(default=None)


class MetricId(ViewBuilderBasedModel, frozen=True):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    scope: Scope
    taxonomy: str
    aggregations_patterns: tuple[AggregationPattern, ...] = Field(min_length=1)
    metrics: list[MetricId] = Field(min_length=1)


@dataclass
class ViewConfig:
    id: str
    calendar_id: str
    location_taxonomy_category: str
    taxonomy_id: str
    aggregation_patterns: tuple[AggregationPattern, ...]
    extra_locations: list[str] = field(default_factory=list)
    full_metric_ids: list[str] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)

    def populate_with_metrics(self, catalogs: list[Catalog]) -> None:
        logging.debug(f"Fetching {len(self.full_metric_ids)} metric(s) from catalogs")
        catalogs_by_id = {catalog.id: catalog for catalog in catalogs}
        for full_metric_id in self.full_metric_ids:
            if full_metric_id.count(".") != 1 or full_metric_id.startswith(".") or full_metric_id.endswith("."):
                raise ValueError(f"Invalid metric id '{full_metric_id}'. Expected format '<catalog_id>.<metric_id>'")
            catalog_id, metric_id = full_metric_id.split(".", 1)
            self.metrics.append(catalogs_by_id[catalog_id].get_metric(metric_id))

    def get_metrics(self) -> list[Metric]:
        return self.metrics


def load_view_config(config_file_path: Path) -> ViewConfig:
    logging.info(f"Loading view config from {config_file_path}")
    raw_view_config = load_view_config_from_yaml(config_file_path)

    view_config = ViewConfig(
        id=raw_view_config.id,
        calendar_id=raw_view_config.scope.calendar,
        location_taxonomy_category=raw_view_config.scope.location.taxonomy_category,
        taxonomy_id=raw_view_config.taxonomy,
        aggregation_patterns=raw_view_config.aggregations_patterns,
        full_metric_ids=[metric.id for metric in raw_view_config.metrics],
        extra_locations=[loc.id for loc in (raw_view_config.scope.extra_locations or [])],
    )
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"metrics={len(view_config.full_metric_ids)}"
    )
    return view_config


def load_view_config_from_yaml(view_file_path: Path) -> RawViewConfig:
    logging.info(f"Parsing view config YAML from {view_file_path}")
    with open(view_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "view" not in raw:
        raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
    logging.info(f"View config YAML parsed successfully from {view_file_path}")
    return RawViewConfig.model_validate(raw["view"])


def load_view_configs(view_configs_paths: list[Path]) -> list[ViewConfig]:
    view_configs: list[ViewConfig] = []
    for path in view_configs_paths:
        view_configs.append(load_view_config(path))
    return view_configs
