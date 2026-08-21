# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from argparse import Namespace
from pathlib import Path

from gems_views_builder.input.calendar import Calendar
from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.library import Library
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from tests.conftest import paths_from_dataset


def test_loader_init_has_no_io() -> None:
    """
    Constructor should not touch the filesystem (no glob/yaml/parquet reads).
    """
    missing = Path("/this/path/should/not/exist")
    paths = InputPaths(
        Namespace(
            libraries_dir=missing / "libraries",
            catalogs_dir=missing / "catalogs",
            system=missing / "system.yml",
            calendar=missing / "calendar.csv",
            taxonomy=missing / "taxonomy.yml",
            view_config=missing / "view_config.yml",
            simulation_table=missing / "simulation_table.parquet",
        )
    )
    loader = Loader(paths)
    assert loader.input_paths is paths
    assert loader.input_paths.libraries_dir == missing / "libraries"


def test_loader_load_populates_raw_input_data(test_dataset_dir: Path) -> None:
    raw_input_data = Loader(paths_from_dataset(test_dataset_dir)).load()

    assert isinstance(raw_input_data, RawInputData)
    assert isinstance(raw_input_data.taxonomy, Taxonomy)
    assert isinstance(raw_input_data.view_config, ViewConfig)
    assert isinstance(raw_input_data.libraries, dict)
    assert raw_input_data.libraries
    assert all(isinstance(library, Library) for library in raw_input_data.libraries.values())
    assert isinstance(raw_input_data.system, System)
    assert isinstance(raw_input_data.simulation_table, SimulationTable)
    assert isinstance(raw_input_data.calendar, Calendar)
    assert raw_input_data.catalogs
    assert all(isinstance(catalog, Catalog) for catalog in raw_input_data.catalogs.values())
    assert raw_input_data.view_config.metrics == []


def test_loader_classmethod_load_populates_raw_input_data(test_dataset_dir: Path) -> None:
    loader = Loader(paths_from_dataset(test_dataset_dir))
    raw_input_data = loader.load()

    assert isinstance(raw_input_data, RawInputData)
    assert isinstance(raw_input_data.taxonomy, Taxonomy)
    assert isinstance(raw_input_data.view_config, ViewConfig)
    assert isinstance(raw_input_data.libraries, dict)
    assert raw_input_data.libraries
    assert all(isinstance(library, Library) for library in raw_input_data.libraries.values())
    assert isinstance(raw_input_data.system, System)
    assert isinstance(raw_input_data.simulation_table, SimulationTable)
    assert isinstance(raw_input_data.calendar, Calendar)
    assert raw_input_data.catalogs
    assert all(isinstance(catalog, Catalog) for catalog in raw_input_data.catalogs.values())
    assert raw_input_data.view_config.metrics == []
