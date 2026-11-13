# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
from collections import defaultdict
from concurrent.futures import Future, as_completed
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from gems_views_builder.aggregators.parallel import get_executor
from gems_views_builder.aggregators.scenario_aggregator import aggregate_scenarios
from gems_views_builder.aggregators.time_aggregator import aggregate_time
from gems_views_builder.common import peak_rss_gib
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView


def shared_location_filter(patterns: list[AggregationPattern]) -> list[str] | None:
    """Union of the patterns' location filters, or None if any pattern keeps every location."""
    if not all(pattern.location_filter for pattern in patterns):
        return None
    return sorted({location for pattern in patterns for location in pattern.location_filter or []})


def log_task_time(label: str, seconds: float) -> None:
    logging.info(f"TIMING {label}: {seconds:.3f}s (peak RSS {peak_rss_gib():.2f} GiB)")


class AggregationPatternList:
    """Runs every aggregation pattern of a view config on one metric.

    Each distinct time granularity is aggregated once, all granularities concurrently. As soon as
    one finishes, the scenario steps of all patterns using that granularity start, concurrently
    too. When every pattern of a granularity has a location filter, the time aggregation already
    keeps only the union of their locations.
    """

    def __init__(self, view_config: ViewConfig) -> None:
        self.patterns = list(view_config.aggregation_patterns)
        # Pattern indexes (not patterns) so that two identical patterns stay two outputs.
        self.pattern_indexes_by_granularity: dict[TimeGranularity, list[int]] = defaultdict(list)
        for index, pattern in enumerate(self.patterns):
            self.pattern_indexes_by_granularity[pattern.time_granularity].append(index)
        self._root_dir = Path(tempfile.mkdtemp())
        # The scenario views are read by accumulate_on_disk() after this object is gone: only remove
        # them at interpreter exit (time-aggregated intermediates are removed as soon as unused).
        atexit.register(rmtree, self._root_dir, True)

    def run(self, metric_view: MetricView, metric: Metric) -> list[TemporalMetricView]:
        executor = get_executor()
        time_paths = {
            granularity: self._root_dir / f"{granularity.value}_{metric.id}_{uuid4()}.parquet"
            for granularity in self.pattern_indexes_by_granularity
        }
        time_futures: dict[Future[float], TimeGranularity] = {
            executor.submit(
                aggregate_time,
                metric_view.persistence_path,
                time_paths[granularity],
                granularity,
                metric.time_operator,
                shared_location_filter([self.patterns[index] for index in indexes]),
            ): granularity
            for granularity, indexes in self.pattern_indexes_by_granularity.items()
        }

        scenario_futures: dict[Future[float], int] = {}
        output_paths: dict[int, Path] = {}
        for time_future in as_completed(time_futures):
            granularity = time_futures[time_future]
            log_task_time(f"[{metric.id}] time aggregation {granularity.value}", time_future.result())
            for index in self.pattern_indexes_by_granularity[granularity]:
                pattern = self.patterns[index]
                output_paths[index] = self._root_dir / f"{pattern.id}_{metric.id}_{uuid4()}.parquet"
                scenario_future = executor.submit(
                    aggregate_scenarios,
                    time_paths[granularity],
                    output_paths[index],
                    pattern.scenario,
                    pattern.location_filter,
                )
                scenario_futures[scenario_future] = index

        for scenario_future in as_completed(scenario_futures):
            pattern_id = self.patterns[scenario_futures[scenario_future]].id
            log_task_time(f"[{metric.id}] scenario step {pattern_id}", scenario_future.result())

        for time_path in time_paths.values():
            time_path.unlink(missing_ok=True)
        return [
            TemporalMetricView(persistence_path=output_paths[index], aggregation_pattern_id=pattern.id)
            for index, pattern in enumerate(self.patterns)
        ]
