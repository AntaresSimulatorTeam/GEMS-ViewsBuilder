# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gems_views_builder.input.view_config import AggregationPattern, ViewConfig

# Basic combinatorial formula 5 * 2 = 10 at maximum
# 5 time granularities
# 2 scenario types
ALLOWED_PATTERN_COUNT = 10


@dataclass
class ViewConfigsAggregationPatternsValidator:
    view_configs: list[ViewConfig]

    def validate(self) -> None:
        for view_config in self.view_configs:
            self._validate_patterns(view_config.aggregation_patterns)

    def _validate_patterns(self, aggregation_patterns: tuple[AggregationPattern, ...]) -> None:
        if len(aggregation_patterns) > ALLOWED_PATTERN_COUNT:
            raise ValueError(f"At most {ALLOWED_PATTERN_COUNT} patterns are allowed")

        pattern_combinations = set()
        for pattern in aggregation_patterns:
            if (pattern.time_granularity, pattern.scenario) in pattern_combinations:
                raise ValueError(f"Pattern ({pattern.time_granularity}, {pattern.scenario}) is already defined")
            pattern_combinations.add((pattern.time_granularity, pattern.scenario))
