# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import os
import tempfile
from dataclasses import dataclass

import polars as pl

from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ScenarioAggregation
from gems_views_builder.into_scenario_view import ScenarioOperator, make_scenario_operator, to_scenario_view
from gems_views_builder.metric_view import MetricView


# # Combinatorial formula 5 * 2 = 10 at maximum
# # 5 time granularities
# # 2 scenario types
@dataclass
class ScenarioAggregationStep:
    time_aggregator: TimeAggregator
    scenario_operator: ScenarioOperator
    spatial_filter: list[str] | None = None


def spatial_filter(metric_view: MetricView, spatial_filter: list[str] | None) -> None:
    if spatial_filter is None:
        return

    try:
        file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
        os.close(file_descriptor)

        view = pl.scan_parquet(metric_view.persistence_path).filter(pl.col("metric_location").is_in(spatial_filter))
        view.sink_parquet(
            tmp_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )

        os.replace(src=tmp_path, dst=metric_view.persistence_path)
    except Exception:
        # If something goes wrong, remove the temporary file to avoid leaving a half-written file
        os.remove(tmp_path)
    logging.info(f"Spatial filter applied to {metric_view.persistence_path}")


class ScenarioAggregationRunner:
    def __init__(self, scenario_aggregations: tuple[ScenarioAggregation, ...]) -> None:
        self.scenario_aggregation_steps = [
            ScenarioAggregationStep(
                time_aggregator=TimeAggregator(scenario_aggregation.time, scenario_aggregation.id),
                scenario_operator=make_scenario_operator(scenario_aggregation.scenario),
                spatial_filter=scenario_aggregation.spatial_filter,
            )
            for scenario_aggregation in scenario_aggregations
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> list[MetricView]:
        scenario_aggregation_views: list[MetricView] = []
        for step in self.scenario_aggregation_steps:
            temporal_metric_view = step.time_aggregator.run(metric_view, metric)
            # # Open question , we could merge this 2 steps to avoid multiple I/O disk operations
            to_scenario_view(temporal_metric_view, step.scenario_operator)
            spatial_filter(temporal_metric_view, step.spatial_filter)
            scenario_aggregation_views.append(temporal_metric_view)

        return scenario_aggregation_views
