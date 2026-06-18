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

from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.loader import Loader


def test_loader_init_has_no_io() -> None:
    """
    Constructor should not touch the filesystem (no glob/yaml/parquet reads).
    """
    missing = Path("/this/path/should/not/exist")
    loader = Loader(missing)
    assert loader.input_data_path == missing


def test_loader_load_populates_input_data(test_dataset_dir: Path) -> None:
    input_data = Loader(test_dataset_dir).load()

    assert isinstance(input_data, InputData)
    assert input_data.input_data_path == test_dataset_dir
    assert isinstance(input_data.taxonomy, Taxonomy)
    assert isinstance(input_data.view_config, ViewConfig)
    assert isinstance(input_data.catalogs, dict)
    assert isinstance(input_data.library, Library)
    assert isinstance(input_data.system, System)
    assert isinstance(input_data.filtered_st, FilteredSimulationTable)
    assert isinstance(loader.catalogs, dict)
    assert loader.catalogs
    for catalog_id in loader.view_config.catalog_ids:
        assert catalog_id in loader.catalogs
        assert isinstance(loader.catalogs[catalog_id], Catalog)


def test_loader_classmethod_load_populates_input_data(test_dataset_dir: Path) -> None:
    loader = Loader(test_dataset_dir)
    input_data = loader.load()

    assert isinstance(input_data, InputData)
    assert input_data.input_data_path == test_dataset_dir
    assert isinstance(input_data.taxonomy, Taxonomy)
    assert isinstance(input_data.view_config, ViewConfig)
    assert isinstance(input_data.catalogs, dict)
    assert isinstance(input_data.library, Library)
    assert isinstance(input_data.system, System)
    assert isinstance(input_data.filtered_st, FilteredSimulationTable)
