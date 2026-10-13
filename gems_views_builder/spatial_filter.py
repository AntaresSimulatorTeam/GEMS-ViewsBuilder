# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl
from gems_views_builder import MetricView


@dataclass
class SpatialFilter:
    locations: list[str] | None


def apply_spatial_filter(metric_view: MetricView, spatial_filter: SpatialFilter) -> pl.LazyFrame:
    if spatial_filter.locations:
        return metric_view.lazy_data_frame().filter(pl.col("metric_location").is_in(spatial_filter.locations))
    return metric_view.lazy_data_frame()
