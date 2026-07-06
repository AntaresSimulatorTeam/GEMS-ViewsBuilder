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
from pathlib import Path

from gems_views_builder.view.view_sinker import CsvViewSinker, ParquetViewSinker, ViewSinker


class ViewSinkerFactory:
    def __init__(self, output_path: Path, output_format: str):
        self.output_path = output_path
        self.output_format = output_format

    def make(self) -> ViewSinker:
        if self.output_format == "parquet":
            return ParquetViewSinker(self.output_path, self.output_format)
        elif self.output_format == "csv":
            return CsvViewSinker(self.output_path, self.output_format)
        else:
            raise ValueError(f"Invalid output format: {self.output_format}")
