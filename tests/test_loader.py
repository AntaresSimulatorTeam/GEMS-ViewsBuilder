# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from gems_views_builder.input.calendar import Calendar
from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.library import Library
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.input_layout import InputLayout
from gems_views_builder.loader import Loader


def test_loader_init_has_no_io() -> None:
    """
    Constructor should not touch the filesystem (no glob/yaml/parquet reads).
    """
    missing = Path("/this/path/should/not/exist")
    layout = InputLayout(missing)
    loader = Loader(layout)
    assert loader.input_layout is layout
    assert loader.input_layout.root_dir == missing


def test_loader_load_populates_raw_input_data(test_dataset_dir: Path) -> None:
    raw_input_data = Loader(InputLayout(test_dataset_dir)).load()

    assert isinstance(raw_input_data, RawInputData)
    assert raw_input_data.input_data_path == test_dataset_dir
    assert isinstance(raw_input_data.taxonomy, Taxonomy)
    assert isinstance(raw_input_data.view_config, ViewConfig)
    assert isinstance(raw_input_data.library, Library)
    assert isinstance(raw_input_data.system, System)
    assert isinstance(raw_input_data.simulation_table, SimulationTable)
    assert isinstance(raw_input_data.calendar, Calendar)
    assert raw_input_data.catalogs
    assert all(isinstance(catalog, Catalog) for catalog in raw_input_data.catalogs.values())
    assert raw_input_data.view_config.metrics == []


def test_loader_classmethod_load_populates_raw_input_data(test_dataset_dir: Path) -> None:
    loader = Loader(InputLayout(test_dataset_dir))
    raw_input_data = loader.load()

    assert isinstance(raw_input_data, RawInputData)
    assert raw_input_data.input_data_path == test_dataset_dir
    assert isinstance(raw_input_data.taxonomy, Taxonomy)
    assert isinstance(raw_input_data.view_config, ViewConfig)
    assert isinstance(raw_input_data.library, Library)
    assert isinstance(raw_input_data.system, System)
    assert isinstance(raw_input_data.simulation_table, SimulationTable)
    assert isinstance(raw_input_data.calendar, Calendar)
    assert raw_input_data.catalogs
    assert all(isinstance(catalog, Catalog) for catalog in raw_input_data.catalogs.values())
    assert raw_input_data.view_config.metrics == []
