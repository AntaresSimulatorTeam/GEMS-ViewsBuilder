# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import os
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait

from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.view.views_builder import ViewBuilder


class ParallelViewsBuilderExecutor:
    def __init__(self, view_builders: list[ViewBuilder], parallel_mode: str):
        self.view_builders = list(view_builders)
        self.num_of_available_cores = get_num_of_cores_per_mode(parallel_mode)
        self.metric_views: list[TemporalMetricView] = []
        self.currently_building: set[Future[list[TemporalMetricView]]] = set()

    def build(self) -> list[TemporalMetricView]:
        with ThreadPoolExecutor(max_workers=self.num_of_available_cores) as job_executor:
            while self.view_builders or self.currently_building:
                self._schedule_new_jobs(job_executor)
                finished_jobs, _ = wait(self.currently_building, return_when=FIRST_COMPLETED)
                self._collect_finished_jobs(finished_jobs)
        return self.metric_views

    def _schedule_new_jobs(self, job_executor: ThreadPoolExecutor) -> None:
        while self.view_builders and self.num_of_available_cores > 0:
            view_builder = self.view_builders.pop()
            job = job_executor.submit(view_builder.build)
            self.num_of_available_cores -= 1
            self.currently_building.add(job)

    def _collect_finished_jobs(
        self,
        finished_jobs: set[Future[list[TemporalMetricView]]],
    ) -> None:
        for job in finished_jobs:
            self.currently_building.remove(job)
            self.metric_views.extend(job.result())
            self.num_of_available_cores += 1


def get_num_of_cores_per_mode(parallel_mode: str) -> int:
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
