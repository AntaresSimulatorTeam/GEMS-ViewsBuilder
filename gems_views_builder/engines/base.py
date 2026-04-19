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

"""Abstract backend engine and factory for multi-backend benchmarking."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal

from gems_views_builder.catalog import TermsOperator, TimeOperator

BackendName = Literal["polars", "duckdb", "pyarrow", "spark"]

# Shared parquet write defaults used across all engines.
PARQUET_COMPRESSION = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000


class DataEngine(ABC):
    """
    Abstract base for interchangeable compute backends.

    Each engine receives file paths as inputs and writes results to disk.
    ViewBuilder owns all path construction; engines own all data transformation.
    """

    @abstractmethod
    def filter_simulation_table(
        self,
        simulation_path: Path,
        calendar_path: Path,
        output_path: Path,
    ) -> None:
        """
        Join simulation table with calendar (inner join on absolute_time_index,
        filter where block matches), append non-time-dependent rows with a null
        granular_date, and write the combined result to output_path.
        """

    @abstractmethod
    def write_metric_structure(
        self,
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        """Serialise metric-structure rows to a parquet file at output_path."""

    @abstractmethod
    def aggregate_metric_terms(
        self,
        filtered_sim_path: Path,
        metric_structure_path: Path,
        operator: TermsOperator,
        output_path: Path,
    ) -> None:
        """
        Right-join filtered simulation table with metric structure on
        (component, output), group by metric/location/breakdown/time/scenario,
        aggregate values with operator (SUM or MEAN), write result to output_path.
        """

    @abstractmethod
    def aggregate_metric_temporally(
        self,
        metric_view_path: Path,
        operator: TimeOperator,
        output_path: Path,
    ) -> None:
        """
        Read metric view, rename granular_date → view_date, group by
        metric/location/breakdown/date/scenario, aggregate with operator,
        write result to output_path.
        """

    @abstractmethod
    def consolidate(
        self,
        chunk_paths: list[Path],
        output_path: Path,
    ) -> None:
        """Concatenate all chunk parquets into a single output_path file."""


def make_engine(name: BackendName) -> DataEngine:
    """Instantiate the requested backend engine."""
    match name:
        case "polars":
            from gems_views_builder.engines.polars_engine import PolarsEngine

            return PolarsEngine()
        case "duckdb":
            from gems_views_builder.engines.duckdb_engine import DuckDBEngine

            return DuckDBEngine()
        case "pyarrow":
            from gems_views_builder.engines.pyarrow_engine import PyArrowEngine

            return PyArrowEngine()
        case "spark":
            from gems_views_builder.engines.spark_engine import SparkEngine

            return SparkEngine()
        case _:
            raise ValueError(f"Unknown backend: {name!r}. Choose from: polars, duckdb, pyarrow, spark")
