# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from concurrent.futures import ThreadPoolExecutor
from itertools import repeat

from gems_views_builder.input.view_building_input import ViewBuildingInput
from gems_views_builder.view import ViewBuilder, ViewSinker, accumulate_on_disk


def view_building_process(view_building_input: ViewBuildingInput, view_sinker: ViewSinker) -> None:
    metric_views = ViewBuilder(view_building_input).build()
    accumulate_on_disk(metric_views, view_sinker)
    # Drop this config's intermediate parquet files before the next config is built.
    del metric_views


class ParallelViewsBuilderExecutor:
    def __init__(self, view_building_inputs: list[ViewBuildingInput], view_sinker: ViewSinker) -> None:
        self.view_building_inputs = view_building_inputs
        self.view_sinker = view_sinker

    def execute(self, num_workers: int) -> None:
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for _ in executor.map(
                view_building_process,
                self.view_building_inputs,
                repeat(self.view_sinker),
            ):
                ...
