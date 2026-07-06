# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from dataclasses import dataclass

import polars as pl

from gems_views_builder.metric_view import MetricView
from gems_views_builder.view.view_sinker import ViewSinker  # noqa: E402

@dataclass
class View:
    dataframe: pl.LazyFrame
    # # Here we could store ViewConfig in future versions





def accumulate_on_disk(metric_views: list[MetricView], sinker: ViewSinker) -> View:
    merged = pl.scan_parquet([v.persistence_path for v in metric_views])
    return sinker.sink(merged)
