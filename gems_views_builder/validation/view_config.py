# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.view_config import ViewConfig

# 5 time granularities and 2 scenario types.
ALLOWED_PATTERN_COUNT = 10


def validate_view_configs(view_configs: list[ViewConfig]) -> None:
    validate_unique_ids(view_configs)
    validate_view_configs_aggregation_patterns(view_configs)


def validate_unique_ids(view_configs: list[ViewConfig]) -> None:
    view_config_ids = set()
    for view_config in view_configs:
        if view_config.id in view_config_ids:
            raise ValueError(f"View config {view_config.id!r} is defined multiple times")
        view_config_ids.add(view_config.id)


def validate_view_configs_aggregation_patterns(view_configs: list[ViewConfig]) -> None:
    validate_unique_aggregation_pattern_ids(view_configs)
    validate_aggregation_pattern_combinations(view_configs)


def validate_unique_aggregation_pattern_ids(view_configs: list[ViewConfig]) -> None:
    for view_config in view_configs:
        pattern_ids: set[str] = set()
        for pattern in view_config.aggregation_patterns:
            if pattern.id in pattern_ids:
                raise ValueError(f"Aggregation pattern {pattern.id!r} is defined multiple times")
            pattern_ids.add(pattern.id)


def validate_aggregation_pattern_combinations(view_configs: list[ViewConfig]) -> None:
    for view_config in view_configs:
        aggregation_patterns = view_config.aggregation_patterns
        if len(aggregation_patterns) > ALLOWED_PATTERN_COUNT:
            raise ValueError(f"At most {ALLOWED_PATTERN_COUNT} patterns are allowed")

        pattern_combinations = set()
        for pattern in aggregation_patterns:
            combination = (pattern.time_granularity, pattern.scenario)
            if combination in pattern_combinations:
                raise ValueError(f"Pattern ({pattern.time_granularity}, {pattern.scenario}) is already defined")
            pattern_combinations.add(combination)
