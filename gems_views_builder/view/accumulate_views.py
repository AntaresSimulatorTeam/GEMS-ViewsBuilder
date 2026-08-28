# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict
from dataclasses import dataclass

import polars as pl

from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import TemporalMetricView


@dataclass
class View:
    dataframe: pl.LazyFrame


from gems_views_builder.view.view_sinker import ViewSinker  # noqa: E402


def group_by_time_granularity(
    metric_views: list[TemporalMetricView],
) -> dict[TimeGranularity, list[TemporalMetricView]]:
    views_by_time_granularity: dict[TimeGranularity, list[TemporalMetricView]] = defaultdict(list)
    for view in metric_views:
        views_by_time_granularity[view.time_granularity].append(view)
    return views_by_time_granularity


def accumulate_views(views: list[TemporalMetricView]) -> pl.LazyFrame:
    return pl.scan_parquet([v.persistence_path for v in views])


def accumulate_on_disk(metric_views: list[TemporalMetricView], sinker: ViewSinker) -> None:
    for time_granularity, views in group_by_time_granularity(metric_views).items():
        sinker.sink(accumulate_views(views), time_granularity)
