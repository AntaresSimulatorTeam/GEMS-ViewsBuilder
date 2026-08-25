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
    # Here will be filter in next PR


class Scope(ViewBuilderBasedModel):
    location: Location
    calendar: str
    extra_locations: list[ExtraLocation] | None = Field(default=None, min_length=0)


class Pattern(ViewBuilderBasedModel):
    id: str
    time_granularity: TimeGranularity
    scenario: bool


class CatalogId(ViewBuilderBasedModel):
    id: str


class MetricId(ViewBuilderBasedModel, frozen=True):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str
    scope: Scope
    aggregations_patterns: tuple[Pattern, ...] = Field(min_length=1)
    catalogs: list[CatalogId]
    metrics: list[MetricId]


@dataclass
class ViewConfig:
    id: str
    calendar_id: str
    location_taxonomy_category: str
    aggregation_patterns: tuple[Pattern, ...]
    catalog_ids: set[str] = field(default_factory=set)
    extra_locations: list[str] = field(default_factory=list)
    metric_ids: list[str] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)

    def fetch_metrics(self, catalogs: dict[str, Catalog]) -> None:
        logging.debug(f"Fetching {len(self.metric_ids)} metric(s) from catalogs")
        for metric_ref in self.metric_ids:
            if "." not in metric_ref or metric_ref.startswith(".") or metric_ref.endswith("."):
                raise ValueError(
                    f"Invalid metric id '{metric_ref}'. "
                    f"Expected format '<catalog_id>.<metric_id>' for catalog {self.catalog_ids}"
                )
            catalog_id, metric_id = metric_ref.split(".", 1)

            if catalog_id not in self.catalog_ids:
                raise ValueError(f"Catalog {catalog_id!r} not found in view config")

            logging.debug(f"Mapped metric {metric_id!r} to catalog {catalog_id!r}")

            self.metrics.append(catalogs[catalog_id].get_metric(metric_id))

    def get_metrics(self) -> list[Metric]:
        return self.metrics


def load_view_config(config_file_path: Path) -> ViewConfig:
    from gems_views_builder.validation.aggregation_patterns_validator import AggregationPatternsValidator

    logging.info(f"Loading view config from {config_file_path}")
    raw_view_config = load_raw_view_config_file(config_file_path)
    AggregationPatternsValidator(raw_view_config.aggregations_patterns).validate()

    view_config = ViewConfig(
        id=raw_view_config.id,
        calendar_id=raw_view_config.scope.calendar,
        location_taxonomy_category=raw_view_config.scope.location.taxonomy_category,
        catalog_ids={c.id for c in raw_view_config.catalogs},
        aggregation_patterns=raw_view_config.aggregations_patterns,
        metric_ids=[metric.id for metric in raw_view_config.metrics],
        extra_locations=[loc.id for loc in (raw_view_config.scope.extra_locations or [])],
    )
    logg_loaded_view_config(view_config)
    return view_config


def logg_loaded_view_config(view_config: ViewConfig) -> None:
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"catalogs={len(view_config.catalog_ids)}, metrics={len(view_config.metrics)}"
    )


def load_raw_view_config_file(view_file_path: Path) -> RawViewConfig:
    logging.info(f"Parsing view config YAML from {view_file_path}")
    with open(view_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "view" not in raw:
        raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
    logging.info(f"View config YAML parsed successfully from {view_file_path}")
    return RawViewConfig.model_validate(raw["view"])
