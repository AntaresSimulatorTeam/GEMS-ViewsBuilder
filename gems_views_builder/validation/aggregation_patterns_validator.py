# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gems_views_builder.input.view_config import Pattern

# Basic combinatorial formula 5 * 2 = 10 at maximum
# 5 time granularities
# 2 scenario types
ALLOWED_PATTERN_COUNT = 10


@dataclass
class AggregationPatternsValidator:
    patterns: tuple[Pattern, ...]

    def validate(self) -> None:
        if len(self.patterns) > ALLOWED_PATTERN_COUNT:
            raise ValueError(f"At most {ALLOWED_PATTERN_COUNT} patterns are allowed")

        pattern_combinations = set()
        for pattern in self.patterns:
            if (pattern.time_granularity, pattern.scenario) in pattern_combinations:
                raise ValueError(f"Pattern ({pattern.time_granularity}, {pattern.scenario}) is already defined")
            pattern_combinations.add((pattern.time_granularity, pattern.scenario))
