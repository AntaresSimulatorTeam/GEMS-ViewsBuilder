# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


class AggregationOperation(ABC):
    def __init__(
        self,
    ) -> None:
        self._root_dir = Path(mkdtemp())
        atexit.register(rmtree, self._root_dir, True)
    @abstractmethod
    def run(self, metric_view: MetricView, metric: Metric) -> MetricView: ...

