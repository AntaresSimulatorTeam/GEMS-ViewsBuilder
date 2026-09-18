# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict

import polars as pl

from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.view.view_sinker import ViewSinker


def group_views(
    metric_views: list[TemporalMetricView],
) -> dict[tuple[str, TimeGranularity], list[TemporalMetricView]]:
    """
    Groups a list of TemporalMetricView objects by their view_config_id and time_granularity.
    """
    grouped_views: dict[tuple[str, TimeGranularity], list[TemporalMetricView]] = defaultdict(list)
    for view in metric_views:
        key = (view.view_config_id, view.time_granularity)
        grouped_views[key].append(view)
    return grouped_views


def accumulate_views(views: list[TemporalMetricView]) -> pl.LazyFrame:
    return pl.scan_parquet([v.persistence_path for v in views])


def accumulate_on_disk(metric_views: list[TemporalMetricView], sinker: ViewSinker) -> None:
    for (view_config_id, time_granularity), views in group_views(metric_views).items():
        accumulated_views = accumulate_views(views)
        save_file_name = f"{view_config_id}_{time_granularity.value}"
        sinker.sink(accumulated_views, save_file_name)
