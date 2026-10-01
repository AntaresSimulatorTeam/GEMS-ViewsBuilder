# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod

import polars as pl

from gems_views_builder.input.catalog import Metric


class AggregationOperator(ABC):
    @abstractmethod
    def run(self, dataframe: pl.LazyFrame, metric: Metric) -> pl.LazyFrame: ...
