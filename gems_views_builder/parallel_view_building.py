# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from gems_views_builder.input.component import Component
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.metric_view import TemporalMetricView


class ParallelViewBuilding:
    def __init__(
        self, view_building_inputs: list[ViewBuildingInputData], components_by_taxon: dict[str, list[Component]]
    ):
        self.view_building_inputs = view_building_inputs
        self.view_building_inputs_num = len(view_building_inputs)
        self.components_by_taxon = components_by_taxon
        self.num_workers = os.cpu_count()

    def build(self) -> dict[str, list[TemporalMetricView]]:
        temporal_metric_views_by_view_config = defaultdict(list)
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            ...
        return temporal_metric_views_by_view_config
