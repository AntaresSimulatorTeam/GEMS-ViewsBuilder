# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

from gems_views_builder.input.raw_input_data import RawInputData

# Basic combinatorial formula 5 * 2 = 10 at maximum
# 5 time granularities
# 2 scenario types
ALLOWED_PATTERN_COUNT = 10


@dataclass
class AggregationPatternsValidator:
    raw_input_data: RawInputData

    def validate(self) -> None:
        aggregation_patterns = self.raw_input_data.view_config.aggregation_patterns
        if len(aggregation_patterns) > ALLOWED_PATTERN_COUNT:
            raise ValueError(f"At most {ALLOWED_PATTERN_COUNT} patterns are allowed")

        pattern_combinations = set()
        for pattern in aggregation_patterns:
            if (pattern.time_granularity, pattern.scenario) in pattern_combinations:
                raise ValueError(f"Pattern ({pattern.time_granularity}, {pattern.scenario}) is already defined")
            pattern_combinations.add((pattern.time_granularity, pattern.scenario))
