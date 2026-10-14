# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from argparse import Namespace
from pathlib import Path

import polars as pl

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
from tests.common import SIMULATION_TABLE_ROW

LIBRARY_YML = """
library:
  id: lib
  port-types:
    - id: flow
      fields:
        - id: flow
  models:
    - id: node
      taxonomy-category: balance
      variables:
        - id: p
          lower-bound: "0"
          upper-bound: "1"
      ports:
        - id: balance_port
          type: flow
      port-field-definitions:
        - port: balance_port
          field: flow
          definition: p
    - id: peer
      taxonomy-category: balance
      ports:
        - id: balance_port
          type: flow
"""

SYSTEM_YML = """
system:
  id: tiny
  components:
    - id: node_a
      model: lib.node
    - id: node_b
      model: lib.peer
  connections:
    - component1: node_a
      port1: balance_port
      component2: node_b
      port2: balance_port
"""

TAXONOMY_YML = """
taxonomy:
  id: my_taxonomy
  description: Minimal taxonomy
  categories:
    - id: balance
      ports:
        - id: balance_port
"""

CATALOG_YML = """
catalog:
  id: catalog
  taxonomy: my_taxonomy
  location:
    taxonomy-category: balance
  metrics-definition:
    - id: LOAD
      terms:
        - taxonomy-category: balance
          output-id: flow
          location-port: balance_port
      terms-operator: sum
      time-operator: sum
"""

VIEW_CONFIG_YML = """
view:
  id: view_area
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
      scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""

CALENDAR_CSV = """absolute_time_index,block,granular_date
0,b1,2026-01-01T00:00:00
"""


def write_minimal_dataset(root: Path) -> InputPaths:
    libraries_dir = root / "libraries"
    catalogs_dir = root / "catalogs"
    libraries_dir.mkdir()
    catalogs_dir.mkdir()
    (libraries_dir / "library.yml").write_text(LIBRARY_YML)
    (catalogs_dir / "catalog.yml").write_text(CATALOG_YML)
    (root / "system.yml").write_text(SYSTEM_YML)
    (root / "taxonomy.yml").write_text(TAXONOMY_YML)
    (root / "view_config.yml").write_text(VIEW_CONFIG_YML)
    (root / "calendar_file.csv").write_text(CALENDAR_CSV)
    pl.DataFrame([SIMULATION_TABLE_ROW]).write_parquet(root / "simulation_table.parquet")
    return InputPaths(
        Namespace(
            libraries_dir=libraries_dir,
            catalogs_dir=catalogs_dir,
            system=root / "system.yml",
            calendar=root / "calendar_file.csv",
            taxonomy=root / "taxonomy.yml",
            view_config=root / "view_config.yml",
            simulation_tables=str(root / "simulation_table.parquet"),
        )
    )


def test_loader_init_has_no_io(tmp_path: Path) -> None:
    """
    Constructor should not touch the filesystem (no glob/yaml/parquet reads).
    """
    missing = Path("/this/path/should/not/exist")
    simulation_table = tmp_path / "simulation_table.parquet"
    simulation_table.touch()
    paths = InputPaths(
        Namespace(
            libraries_dir=missing / "libraries",
            catalogs_dir=missing / "catalogs",
            system=missing / "system.yml",
            calendar=missing / "calendar.csv",
            taxonomy=missing / "taxonomy.yml",
            view_config=missing / "view_config.yml",
            simulation_tables=str(simulation_table),
        )
    )
    loader = Loader(paths)
    assert loader.input_paths is paths
    assert loader.input_paths.libraries_dir == missing / "libraries"


def test_loader_load_populates_raw_input_data(tmp_path: Path) -> None:
    raw_input_data = Loader(write_minimal_dataset(tmp_path)).load()

    assert isinstance(raw_input_data, RawInputData)
    assert isinstance(raw_input_data.taxonomy, Taxonomy)
    assert isinstance(raw_input_data.view_config, ViewConfig)
    assert isinstance(raw_input_data.libraries, dict)
    assert raw_input_data.libraries
    assert all(isinstance(library, Library) for library in raw_input_data.libraries.values())
    assert isinstance(raw_input_data.system, System)
    assert isinstance(raw_input_data.simulation_tables, list)
    assert raw_input_data.simulation_tables
    assert all(isinstance(table, SimulationTable) for table in raw_input_data.simulation_tables)
    assert isinstance(raw_input_data.calendar, Calendar)
    assert raw_input_data.catalogs
    assert all(isinstance(catalog, Catalog) for catalog in raw_input_data.catalogs)
    assert raw_input_data.view_config.metrics == []
