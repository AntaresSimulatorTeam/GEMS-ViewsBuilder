# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict

import polars as pl

from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import MetricView, PersistentMetricView
from gems_views_builder.view.view_sinker import ViewSinker  # noqa: E402


def group_by_time_granularity(
    metric_views: list[MetricView],
) -> dict[TimeGranularity, list[MetricView]]:
    views_by_time_granularity: dict[TimeGranularity, list[MetricView]] = defaultdict(list)
    for view in metric_views:
        views_by_time_granularity[view.time_granularity].append(view)
    return views_by_time_granularity


def cast_into_persistent_views(views: list[MetricView]) -> list[PersistentMetricView]:
    persistent_views = []
    for view in views:
        if isinstance(view, PersistentMetricView):
            persistent_views.append(view)
        else:
            raise TypeError(f"Expected PersistentMetricView, got {type(view)}")
    return persistent_views


def accumulate_views(views: list[MetricView]) -> pl.LazyFrame:
    persistent_views = cast_into_persistent_views(views)
    return pl.scan_parquet([v.persistence_path for v in persistent_views])


def accumulate_on_disk(metric_views: list[MetricView], sinker: ViewSinker) -> None:
    for time_granularity, views in group_by_time_granularity(metric_views).items():
        sinker.sink(accumulate_views(views), time_granularity)
