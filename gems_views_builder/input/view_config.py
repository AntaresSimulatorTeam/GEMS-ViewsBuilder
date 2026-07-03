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


class Scope(ViewBuilderBasedModel):
    taxonomy_category: str | None = Field(None, alias="taxonomy-category")
    calendar: str | None = None


class Aggregation(ViewBuilderBasedModel):
    time: TimeAggregation | None = None


class CatalogId(ViewBuilderBasedModel):
    id: str


class MetricId(ViewBuilderBasedModel):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str
    scope: list[Scope]
    aggregation: list[Aggregation]
    catalog: list[CatalogId]
    metrics: list[MetricId]


@dataclass
class ViewConfig:
    id: str
    input_data_path: Path
    calendar_id: str
    location_taxonomy_category: str | None = None
    catalog_ids: set[str] = field(default_factory=set)
    time_aggregation: TimeAggregation | None = None
    metrics: list[Metric] = field(default_factory=list)  # This will be empty at first load of View Config
    metric_ids_by_catalog: dict[str, set[str]] = field(default_factory=dict)

    def fetch_metrics(self, catalogs: dict[str, Catalog]) -> None:
        for catalog_id in self.metric_ids_by_catalog.keys():
            for metric_id in self.metric_ids_by_catalog[catalog_id]:
                self.metrics.append(catalogs[catalog_id].get_metric(metric_id))


def load_view_config(config_file_path: Path) -> ViewConfig:
    logging.info(f"Loading view config from {config_file_path}")
    raw_view_config = load_raw_view_config_file(config_file_path)
    input_data_path = config_file_path.parent
    location_taxonomy_category = next(
        (item.taxonomy_category for item in raw_view_config.scope if item.taxonomy_category),
        None,
    )
    if location_taxonomy_category is None:
        raise ValueError(
            f"view_config.yml '{raw_view_config.id}': no 'taxonomy-category' found in scope. "
            f"At least one scope entry must define a taxonomy-category"
        )

    calendar_id = next((item.calendar for item in raw_view_config.scope if item.calendar), None)
    if calendar_id is None:
        raise ValueError(
            f"view_config.yml '{raw_view_config.id}': no calendar configured in scope. One calendar must be configured in scope"
        )

    catalog_ids = {c.id for c in raw_view_config.catalog}
    view_config = ViewConfig(
        id=raw_view_config.id,
        input_data_path=input_data_path,
        calendar_id=calendar_id,
        location_taxonomy_category=location_taxonomy_category,
        catalog_ids=catalog_ids,
        time_aggregation=raw_view_config.aggregation[0].time if raw_view_config.aggregation else None,
        metric_ids_by_catalog=group_metrics_by_catalog(catalog_ids, raw_view_config.metrics),
    )
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"catalogs={len(view_config.catalog_ids)}, metric groups={len(view_config.metric_ids_by_catalog)}"
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


def group_metrics_by_catalog(catalog_ids: set[str], metric_ids: list[MetricId]) -> dict[str, set[str]]:
    logging.debug(f"Grouping {len(metric_ids)} metric id(s) by catalog")
    metric_ids_by_catalog: dict[str, set[str]] = defaultdict(set)
    for metric_id in metric_ids:
        if "." not in metric_id.id or metric_id.id.startswith(".") or metric_id.id.endswith("."):
            raise ValueError(
                f"Invalid metric id '{metric_id.id}'. "
                f"Expected format '<catalog_id>.<metric_id>' for catalog {catalog_ids}"
            )
        catalog_id, metric_id_value = metric_id.id.split(".", 1)
        if catalog_id not in catalog_ids:
            raise ValueError(f"Catalog {catalog_id!r} not found in view config")
        metric_ids_by_catalog[catalog_id].add(metric_id_value)
        logging.debug(f"Mapped metric {metric_id!r} to catalog {catalog_id!r}")
    return metric_ids_by_catalog
