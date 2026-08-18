# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.metric_view import MetricView

# Temporal aggregation files are named {time}_{scenario_id}_{metric_id}.
TIME_GRANULARITY_INDEX = 0


@dataclass
class View:
    dataframe: pl.LazyFrame
    # # Here we could store ViewConfig in future versions


from gems_views_builder.view.view_sinker import ViewSinker  # noqa: E402


def time_granularity_from_filename(path: Path) -> str:
    return path.stem.split("_")[TIME_GRANULARITY_INDEX]


def group_by_time_granularity(metric_views: list[MetricView]) -> dict[str, list[MetricView]]:
    views_by_time_granularity: dict[str, list[MetricView]] = defaultdict(list)
    for view in metric_views:
        views_by_time_granularity[time_granularity_from_filename(view.persistence_path)].append(view)
    return views_by_time_granularity


def merge_same_granularity(views_by_specific_granularity: list[MetricView]) -> pl.LazyFrame:
    return pl.scan_parquet([v.persistence_path for v in views_by_specific_granularity])


def accumulate_on_disk(metric_views: list[MetricView], sinker: ViewSinker) -> None:
    for time_granularity, views in group_by_time_granularity(metric_views).items():
        sinker.sink(merge_same_granularity(views), time_granularity)
