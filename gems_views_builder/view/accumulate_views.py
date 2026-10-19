# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict

import polars as pl

from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.view.view_sinker import ViewSinker


def group_views(metric_views: list[TemporalMetricView]) -> dict[tuple[str, str], list[TemporalMetricView]]:
    """Group metric views that share a view config and an aggregation pattern."""
    grouped_views: dict[tuple[str, str], list[TemporalMetricView]] = defaultdict(list)
    for view in metric_views:
        grouped_views[(view.view_config_id, view.aggregation_pattern_id)].append(view)
    return grouped_views


def accumulate_views(views: list[TemporalMetricView]) -> pl.LazyFrame:
    return pl.scan_parquet([v.persistence_path for v in views])


def accumulate_on_disk(metric_views: list[TemporalMetricView], sinker: ViewSinker) -> None:
    for (view_config_id, aggregation_pattern_id), views in group_views(metric_views).items():
        view = views[0]
        accumulated_views = accumulate_views(views)
        save_file_name = (
            f"{view_config_id}_{aggregation_pattern_id}_{view.time_granularity.value}_{str(view.scenario).lower()}"
        )
        sinker.sink(accumulated_views, save_file_name)
