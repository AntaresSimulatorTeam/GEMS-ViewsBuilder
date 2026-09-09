# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import os
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait

from gems_views_builder.input.component import Component
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.metric_view import TemporalMetricView

BuildMetricViewsForViewConfig = Callable[[ViewBuildingInputData, dict[str, list[Component]]], list[TemporalMetricView]]


class ParallelViewsBuilderExecutor:
    def __init__(
        self,
        view_building_inputs: list[ViewBuildingInputData],
        components_by_taxon: dict[str, list[Component]],
        parallel_mode: str,
        build_metric_views_for_view_config: BuildMetricViewsForViewConfig,
    ):
        self.view_building_inputs = view_building_inputs
        self.components_by_taxon = components_by_taxon
        self.num_of_available_cores = self._get_num_of_cores_per_mode(parallel_mode)
        self.build_metric_views_for_view_config = build_metric_views_for_view_config

    def build(self) -> dict[str, list[TemporalMetricView]]:
        currently_building: dict[Future[list[TemporalMetricView]], str] = {}
        temporal_metric_views_by_view_config: dict[str, list[TemporalMetricView]] = defaultdict(list)

        with ThreadPoolExecutor(max_workers=self.num_of_available_cores) as executor:
            while self.view_building_inputs or currently_building:
                self._schedule_new_jobs(executor, currently_building)
                finished_jobs, _ = wait(currently_building, return_when=FIRST_COMPLETED)
                self._collect_finished_jobs(finished_jobs, currently_building, temporal_metric_views_by_view_config)
        return temporal_metric_views_by_view_config

    def _schedule_new_jobs(
        self, executor: ThreadPoolExecutor, currently_building: dict[Future[list[TemporalMetricView]], str]
    ) -> None:
        while self.view_building_inputs and self.num_of_available_cores > 0:
            view_building_input = self.view_building_inputs.pop()
            job = executor.submit(
                self.build_metric_views_for_view_config,
                view_building_input,
                self.components_by_taxon,
            )
            self.num_of_available_cores -= 1
            currently_building[job] = view_building_input.view_config.id

    def _collect_finished_jobs(
        self,
        finished_jobs: set[Future[list[TemporalMetricView]]],
        currently_building: dict[Future[list[TemporalMetricView]], str],
        temporal_metric_views_by_view_config: dict[str, list[TemporalMetricView]],
    ) -> None:
        for job in finished_jobs:
            view_config_id = currently_building.pop(job)
            temporal_metric_views_by_view_config[view_config_id].extend(job.result())
            self.num_of_available_cores += 1

    def _get_num_of_cores_per_mode(self, parallel_mode: str) -> int:
        cpu_count = os.cpu_count() or 1
        match parallel_mode:
            case "minimum":
                return 1
            case "low":
                return max(1, cpu_count // 4)
            case "medium":
                return max(1, cpu_count // 2)
            case "high":
                return max(1, (cpu_count * 3) // 4)
            case "maximum":
                return cpu_count
            case _:
                raise ValueError(f"Unknown parallel mode: {parallel_mode!r}")
