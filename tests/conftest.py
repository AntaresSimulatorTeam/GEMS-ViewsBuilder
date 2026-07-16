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
from typing import cast

import pytest

from gems_views_builder.common import configure_logging

RESOURCES_TEST_FILES_ROOT = Path(__file__).resolve().parent.parent / "resources"
TEST_INPUTS_PATH = RESOURCES_TEST_FILES_ROOT / "tests_inputs"


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging() -> None:
    """Configure logging once for the whole test session (file + console handlers)."""
    configure_logging()


@pytest.fixture(scope="session")
def test_files_root() -> Path:
    if not TEST_INPUTS_PATH.is_dir():
        raise FileNotFoundError(f"Missing test inputs directory: {TEST_INPUTS_PATH}")
    return TEST_INPUTS_PATH


DATASET_REQUIRED_FILES: tuple[str, ...] = (
    "calendar_file.csv",
    "system.yml",
    "taxonomy.yml",
    "view_config.yml",
)

DATASET_LIBRARY_FILES: tuple[str, ...] = ("library.yml",)


def _dataset_dirs(test_inputs_path: Path) -> list[str]:
    return sorted(d.name for d in test_inputs_path.iterdir() if d.is_dir() and _is_valid_dataset_dir(d))


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
    # `request.param` exists only for parametrized fixtures; pytest's public typing
    # does not expose it on `FixtureRequest`.
    dataset_name = cast(str, getattr(request, "param", None))
    dataset_dir = test_files_root / dataset_name
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"{dataset_name} is not a directory in extracted test files")
    if not _is_valid_dataset_dir(dataset_dir):
        raise FileNotFoundError(f"{dataset_name} does not look like a full dataset directory")
    return dataset_dir


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "test_dataset_dir" not in metafunc.fixturenames:
        return

    if not TEST_INPUTS_PATH.is_dir():
        raise FileNotFoundError(f"Missing test inputs directory: {TEST_INPUTS_PATH}")

    dataset_dirs = _dataset_dirs(TEST_INPUTS_PATH)
    if not dataset_dirs:
        raise FileNotFoundError(
            f"No dataset directories found in {TEST_INPUTS_PATH} "
            f"(expected dirs with {list(DATASET_REQUIRED_FILES)} + catalogs/*.yml + simulation_table*.parquet)."
        )

    metafunc.parametrize(
        "test_dataset_dir",
        dataset_dirs,
        ids=dataset_dirs,
        indirect=True,
    )
