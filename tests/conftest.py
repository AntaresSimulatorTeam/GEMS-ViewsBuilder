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

import shutil
import zipfile
from pathlib import Path
from typing import Any, Generator, cast

import pytest

RESOURCES_TEST_FILES_ROOT = Path(__file__).resolve().parent.parent / "resources"
TEST_ZIP_PATH = RESOURCES_TEST_FILES_ROOT / "tests.zip"


@pytest.fixture(scope="session")
def test_files_root(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """
    Unzip heavy test datasets once per session and delete them afterwards.
    """
    if not TEST_ZIP_PATH.is_file():
        raise FileNotFoundError(f"Missing test archive: {TEST_ZIP_PATH}")

    extract_dir = tmp_path_factory.mktemp("unzipped_test_files")
    with zipfile.ZipFile(TEST_ZIP_PATH) as zf:
        zf.extractall(path=extract_dir)

    root = extract_dir / "tests" / "test_inputs"
    try:
        yield root
    finally:
        # Explicit cleanup when everything is done
        shutil.rmtree(extract_dir)


DATASET_REQUIRED_FILES: tuple[str, ...] = (
    "calendar_file.csv",
    "system.yml",
    "taxonomy.yml",
    "view_config.yml",
)

DATASET_LIBRARY_FILES: tuple[str, ...] = ("library.yml",)


def _unwrap_single_top_level_dir(names: list[str]) -> tuple[str | None, list[str]]:
    top_levels = {n.split("/", 1)[0] for n in names if "/" in n}
    prefix = next(iter(top_levels)) if len(top_levels) == 1 else None
    if prefix is None:
        return None, names
    unwrapped = [n[len(prefix) + 1 :] for n in names if n.startswith(prefix + "/")]
    return prefix, unwrapped


def _strip_leading_dir(names: list[str], dirname: str) -> list[str]:
    """
    If all entries are under `<dirname>/...`, strip that leading directory.
    """
    prefix = f"{dirname}/"
    if not names:
        return names
    if all(n.startswith(prefix) for n in names):
        return [n[len(prefix) :] for n in names]
    return names


def _dataset_and_rest(path: str) -> tuple[str, str] | None:
    if "/" not in path:
        return None
    dataset, rest = path.split("/", 1)
    if not dataset:
        return None
    return dataset, rest


def _zip_dataset_dirs(zip_path: Path) -> list[str]:
    """
    Return all top-level directories in the zip that look like full datasets.
    """
    with zipfile.ZipFile(zip_path) as zf:
        raw_names = [n for n in zf.namelist() if n and not n.endswith("/")]
        _, names = _unwrap_single_top_level_dir(raw_names)
        # Our datasets often live under tests/test_inputs/<dataset>/...
        names = _strip_leading_dir(names, "test_inputs")

        required = set(DATASET_REQUIRED_FILES)
        library_files = set(DATASET_LIBRARY_FILES)
        seen_required: dict[str, set[str]] = {}
        has_library: set[str] = set()
        has_catalog_yml: set[str] = set()
        sim_parquet_counts: dict[str, int] = {}

        for path in names:
            parsed = _dataset_and_rest(path)
            if parsed is None:
                continue
            dataset, rest = parsed

            if rest in required:
                seen_required.setdefault(dataset, set()).add(rest)

            if rest in library_files:
                has_library.add(dataset)

            if rest.startswith("catalogs/") and rest.endswith(".yml") and rest.count("/") == 1:
                has_catalog_yml.add(dataset)

            if rest.startswith("simulation_table") and rest.endswith(".parquet") and "/" not in rest:
                sim_parquet_counts[dataset] = sim_parquet_counts.get(dataset, 0) + 1

    dataset_dirs = [
        d
        for d, got in seen_required.items()
        if got == required and d in has_library and d in has_catalog_yml and sim_parquet_counts.get(d, 0) == 1
    ]
    return sorted(dataset_dirs)


def _is_valid_dataset_dir(dataset_dir: Path) -> bool:
    if not all((dataset_dir / rel).is_file() for rel in DATASET_REQUIRED_FILES):
        return False
    if not any((dataset_dir / rel).is_file() for rel in DATASET_LIBRARY_FILES):
        return False
    catalogs_dir = dataset_dir / "catalogs"
    if not catalogs_dir.is_dir():
        return False
    if not list(catalogs_dir.glob("*.yml")):
        return False
    simulation_tables = list(dataset_dir.glob("simulation_table*.parquet"))
    if len(simulation_tables) != 1:
        return False
    return True


@pytest.fixture
def test_dataset_dir(test_files_root: Path, request: pytest.FixtureRequest) -> Path:
    """
    A single dataset directory (one per parametrized run).

    This fixture is parametrized by `pytest_generate_tests` based on the zip content.
    Directories that do not contain the core dataset files are skipped.
    """
    # `request.param` exists only for parametrized fixtures; pytest's public typing
    # does not expose it on `FixtureRequest`.
    dataset_name = cast(str, getattr(request, "param", cast(Any, None)))
    dataset_dir = test_files_root / dataset_name
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"{dataset_name} is not a directory in extracted test files")
    if not _is_valid_dataset_dir(dataset_dir):
        raise FileNotFoundError(f"{dataset_name} does not look like a full dataset directory")
    return dataset_dir


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Any test that requests `test_dataset_dir` will run once per dataset found in tests.zip.
    """
    if "test_dataset_dir" not in metafunc.fixturenames:
        return

    if not TEST_ZIP_PATH.is_file():
        raise FileNotFoundError(f"Missing test archive: {TEST_ZIP_PATH}")

    dataset_dirs = _zip_dataset_dirs(TEST_ZIP_PATH)
    if not dataset_dirs:
        raise FileNotFoundError(
            f"No dataset directories found in {TEST_ZIP_PATH} "
            f"(expected dirs with {list(DATASET_REQUIRED_FILES)} + catalogs/*.yml + simulation_table*.parquet)."
        )

    metafunc.parametrize(
        "test_dataset_dir",
        dataset_dirs,
        ids=dataset_dirs,
        indirect=True,
    )
