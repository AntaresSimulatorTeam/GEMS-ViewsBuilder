# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import yaml

from gems_views_builder.input.view_config import RawViewConfig, ViewConfig


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
