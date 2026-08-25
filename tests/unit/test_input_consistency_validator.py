# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from argparse import Namespace
from pathlib import Path

import pytest

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from gems_views_builder.validation.input_consistency_validator import InputConsistencyValidator


def _load_raw_input_data(test_dataset_dir: Path) -> RawInputData:
    input_paths = InputPaths(
        Namespace(
            libraries_dir=test_dataset_dir / "libraries",
            catalogs_dir=test_dataset_dir / "catalogs",
            system=test_dataset_dir / "system.yml",
            calendar=test_dataset_dir / "calendar_file.csv",
            taxonomy=test_dataset_dir / "taxonomy.yml",
            view_config=test_dataset_dir / "view_config.yml",
            simulation_table=next(test_dataset_dir.glob("simulation_table*")),
        )
    )
    return Loader(input_paths).load()


def test_input_consistency_validator_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    raw_input_data = _load_raw_input_data(test_dataset_dir)

    InputConsistencyValidator(raw_input_data).validate()


def test_input_consistency_validator_raises_on_view_config_taxonomy_mismatch(test_dataset_dir: Path) -> None:
    raw_input_data = _load_raw_input_data(test_dataset_dir)
    raw_input_data.view_config.taxonomy_id = "wrong_taxonomy"

    with pytest.raises(ValueError, match="references taxonomy"):
        InputConsistencyValidator(raw_input_data).validate()
