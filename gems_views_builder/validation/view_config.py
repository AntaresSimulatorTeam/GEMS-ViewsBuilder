# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.validation.aggregation_patterns_validator import ViewConfigsAggregationPatternsValidator


def validate_view_configs(view_configs: list[ViewConfig]) -> None:
    validate_unique_ids(view_configs)
    validate_full_metric_ids(view_configs)
    ViewConfigsAggregationPatternsValidator(view_configs).validate()


def validate_unique_ids(view_configs: list[ViewConfig]) -> None:
    view_config_ids = set()
    for view_config in view_configs:
        if view_config.id in view_config_ids:
            raise ValueError(f"View config {view_config.id!r} is defined multiple times")
        view_config_ids.add(view_config.id)


def validate_full_metric_ids(view_configs: list[ViewConfig]) -> None:
    for view_config in view_configs:
        for full_metric_id in view_config.full_metric_ids:
            if full_metric_id.count(".") != 1 or full_metric_id.startswith(".") or full_metric_id.endswith("."):
                raise ValueError(f"Invalid metric id '{full_metric_id}'. Expected format '<catalog_id>.<metric_id>'")
