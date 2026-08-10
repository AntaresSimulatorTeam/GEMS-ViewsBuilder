# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl

from gems_views_builder.metric_view import MetricView


@dataclass
class View:
    dataframe: pl.LazyFrame
    # # Here we could store ViewConfig in future versions


from gems_views_builder.view.view_sinker import ViewSinker  # noqa: E402


def accumulate_on_disk(metric_views: list[MetricView], sinker: ViewSinker) -> View:
    merged = pl.scan_parquet([v.persistence_path for v in metric_views])
    return sinker.sink(merged)
