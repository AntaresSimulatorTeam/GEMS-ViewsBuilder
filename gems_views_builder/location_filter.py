# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl


@dataclass
class LocationFilter:
    locations: list[str] | None


def apply_location_filter(metric_view: pl.LazyFrame, location_filter: LocationFilter) -> pl.LazyFrame:
    if location_filter.locations:
        return metric_view.filter(pl.col("metric_location").is_in(location_filter.locations))
    return metric_view
