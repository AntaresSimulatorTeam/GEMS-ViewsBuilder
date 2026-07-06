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

import pytest

from gems_views_builder.view import CsvViewSinker, ParquetViewSinker, ViewSinker, ViewSinkerFactory


def test_view_sinker_cannot_be_instantiated(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="abstract"):
        ViewSinker(tmp_path, "parquet")


@pytest.mark.parametrize(
    ("output_format", "expected_type"),
    [
        ("parquet", ParquetViewSinker),
        ("csv", CsvViewSinker),
    ],
)
def test_view_sinker_factory(tmp_path: Path, output_format: str, expected_type: type[ViewSinker]) -> None:
    sinker = ViewSinkerFactory(tmp_path, output_format).make()
    assert isinstance(sinker, expected_type)


def test_view_sinker_factory_invalid_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid output format"):
        ViewSinkerFactory(tmp_path, "xml").make()
