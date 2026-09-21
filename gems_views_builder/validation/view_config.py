# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.validation.aggregation_patterns_validator import ViewConfigsAggregationPatternsValidator


def validate_view_configs(view_configs: list[ViewConfig]) -> None:
    validate_unique_ids(view_configs)
    ViewConfigsAggregationPatternsValidator(view_configs).validate()


def validate_unique_ids(view_configs: list[ViewConfig]) -> None:
    view_config_ids = set()
    for view_config in view_configs:
        if view_config.id in view_config_ids:
            raise ValueError(f"View config {view_config.id!r} is defined multiple times")
        view_config_ids.add(view_config.id)
