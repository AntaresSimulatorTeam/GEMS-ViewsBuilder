# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.view import CsvViewSinker, ParquetViewSinker, ViewSinker, ViewSinkerFactory


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
