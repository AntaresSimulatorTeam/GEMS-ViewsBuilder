# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

from gems_views_builder.view.view_sinker import CsvViewSinker, ParquetViewSinker, ViewSinker


class ViewSinkerFactory:
    def __init__(self, output_path: Path, output_format: str):
        self.output_path = output_path
        self.output_format = output_format

    def make(self) -> ViewSinker:
        if self.output_format == "parquet":
            return ParquetViewSinker(self.output_path)
        elif self.output_format == "csv":
            return CsvViewSinker(self.output_path)
        else:
            raise ValueError(f"Invalid output format: {self.output_format}")
