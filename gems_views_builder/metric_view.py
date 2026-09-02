# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path
from gems_views_builder.input.view_config import TimeGranularity


@dataclass
class MetricView:
    """View for a single computed metric, stored as a parquet file."""

    persistence_path: Path

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)


@dataclass
class TemporalMetricView(MetricView):
    time_granularity: TimeGranularity

