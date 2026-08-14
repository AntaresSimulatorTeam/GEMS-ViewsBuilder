# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from argparse import Namespace
from pathlib import Path
from typing import cast

import pytest

from gems_views_builder.common import configure_logging
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.validation.input_paths_validator import InputPathsValidator

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


def paths_from_dataset(dataset_dir: Path) -> InputPaths:
    """Build InputPaths from a flat test dataset directory."""
    return InputPaths(
        Namespace(
            libraries_dir=dataset_dir / "libraries",
            catalogs_dir=dataset_dir / "catalogs",
            system=dataset_dir / "system.yml",
            calendar=dataset_dir / "calendar_file.csv",
            taxonomy=dataset_dir / "taxonomy.yml",
            view_config=dataset_dir / "view_config.yml",
            simulation_table=next(dataset_dir.glob("simulation_table*")),
        )
    )


def _dataset_dirs(test_inputs_path: Path) -> list[str]:
    return sorted(d.name for d in test_inputs_path.iterdir() if d.is_dir() and is_valid_dataset_dir(d))


def is_valid_dataset_dir(dataset_dir: Path) -> bool:
    try:
        paths = paths_from_dataset(dataset_dir)
        InputPathsValidator(paths).validate()
    except (OSError, ValueError, StopIteration):
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
    if not is_valid_dataset_dir(dataset_dir):
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
            "(expected a directory that satisfies InputPathsValidator "
        )

    metafunc.parametrize(
        "test_dataset_dir",
        dataset_dirs,
        ids=dataset_dirs,
        indirect=True,
    )
