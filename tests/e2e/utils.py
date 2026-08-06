# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import polars as pl

from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


def make_results_dir(tmp_path: Path) -> Path:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return results_dir


def fetch_view(results_dir: Path) -> pl.DataFrame:
    return pl.read_parquet(next(results_dir.glob("view*.parquet")))


def make_raw_component(component_id: str, model_id: str, properties: dict[str, str]) -> Any:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model_id), properties=properties)


def make_raw_connection(component1: str, port1: str, component2: str, port2: str) -> Any:
    return SimpleNamespace(component1=component1, port1=port1, component2=component2, port2=port2)


def make_filtered_simulation_table(
    rows: list[tuple[str, str, int, datetime, float]], tmp_path: Path
) -> FilteredSimulationTable:
    """Build a FilteredSimulationTable directly, bypassing calendar filtering (out of scope here)."""
    n = len(rows)
    dataframe = pl.DataFrame(
        {
            "block": ["b1"] * n,
            "component": [r[0] for r in rows],
            "output": [r[1] for r in rows],
            "absolute_time_index": list(range(1, n + 1)),
            "block_time_index": list(range(1, n + 1)),
            "scenario_index": [r[2] for r in rows],
            "value": [r[4] for r in rows],
            "basis_status": ["ok"] * n,
            "granular_date": [r[3] for r in rows],
        },
        schema_overrides={"granular_date": pl.Datetime},
    )
    sim_table_dir = tmp_path / "filtered_simulation_table"
    sim_table_dir.mkdir()
    path = sim_table_dir / "filtered.parquet"
    dataframe.write_parquet(path)
    return FilteredSimulationTable(path, pl.scan_parquet(path))


def build_input_data(
    input_dir: Path,
    raw_components: list[Any],
    raw_connections: list[Any],
    taxonomy_category_by_model: dict[str, str],
    view_config: ViewConfig,
    filtered_st: FilteredSimulationTable,
) -> InputData:
    """
    Build a real InputData, skipping only the disk-reading Loader.load() step:
    system/library/taxonomy are minimal but real objects, populated with just
    enough to drive the pipeline steps under test.
    """
    return InputData(
        input_data_path=input_dir,
        taxonomy=Taxonomy(id="taxonomy"),
        library=Library(
            id="lib",
            description="",
            port_types=[],
            models={},
            models_by_taxonomy_category={},
            taxonomy_category_by_model=taxonomy_category_by_model,
        ),
        system=cast(Any, SimpleNamespace(components=raw_components, connections=raw_connections)),
        view_config=view_config,
        filtered_st=filtered_st,
    )
