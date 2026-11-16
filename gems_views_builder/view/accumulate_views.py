# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict

import polars as pl

from gems_views_builder.metric_view import MetricView, PersistentMetricView
from gems_views_builder.view.view_sinker import ViewSinker


def group_views(
    metric_views: list[MetricView],
) -> dict[tuple[str, str], list[MetricView]]:
    """Group metric views by view config and aggregation pattern."""
    grouped_views: dict[tuple[str, str], list[MetricView]] = defaultdict(list)
    for view in metric_views:
        grouped_views[(view.view_config_id, view.aggregation_pattern_id)].append(view)
    return grouped_views


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
    for (view_config_id, aggregation_pattern_id), views in group_views(metric_views).items():
        accumulated_views = accumulate_views(views)
        save_file_name = f"{view_config_id}--{aggregation_pattern_id}"
        sinker.sink(accumulated_views, save_file_name)
