# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl


@dataclass
class SpatialFilter:
    locations: list[str] | None


def apply_spatial_filter(metric_view: pl.LazyFrame, spatial_filter: SpatialFilter) -> pl.LazyFrame:
    if spatial_filter.locations is None:
        return metric_view

    return metric_view.filter(pl.col("metric_location").is_in(spatial_filter.locations))
