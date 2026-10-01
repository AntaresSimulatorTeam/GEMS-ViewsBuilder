# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.paths_resolver import PathsResolver


def test_resolves_matching_files(tmp_path: Path) -> None:
    catalogs_dir = tmp_path / "catalogs"
    catalogs_dir.mkdir()
    first = catalogs_dir / "catalog-a.yml"
    second = catalogs_dir / "catalog-b.yml"
    first.touch()
    second.touch()
    (catalogs_dir / "notes.txt").touch()

    resolved = PathsResolver(str(catalogs_dir / "catalog-*.yml")).resolve()

    assert resolved == [second, first]


def test_raises_when_directory_is_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "catalog-*.yml"
    with pytest.raises(NotADirectoryError, match="Directory does not exist"):
        PathsResolver(str(missing)).resolve()
