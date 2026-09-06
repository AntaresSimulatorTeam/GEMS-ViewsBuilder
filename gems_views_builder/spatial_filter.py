# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl


@dataclass
class SpatialFilter:
    locations: list[str] | None

    def apply_spatial_filter(self, dataframe: pl.LazyFrame) -> pl.LazyFrame:
        if self.locations:
            return dataframe.filter(pl.col("metric_location").is_in(self.locations))
        return dataframe
