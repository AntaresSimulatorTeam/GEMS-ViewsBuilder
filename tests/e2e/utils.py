# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import polars as pl

from gems_views_builder.input.calendar import Calendar
from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.library import Library
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


def create_results_dir(tmp_path: Path) -> Path:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return results_dir


def fetch_view(results_dir: Path) -> pl.DataFrame:
    return pl.read_parquet(next(results_dir.glob("view*.parquet")))


def values_by_day(df: pl.DataFrame) -> dict[datetime, float]:
    return dict(zip(df["view_date"].to_list(), df["metric_value"].to_list()))


def make_raw_component(component_id: str, model_id: str, properties: dict[str, str]) -> Any:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model_id), properties=properties)


def make_raw_connection(component1: str, port1: str, component2: str, port2: str) -> Any:
    return SimpleNamespace(component1=component1, port1=port1, component2=component2, port2=port2)


def make_simulation_table(rows: list[tuple[str, str, int, datetime, float]]) -> SimulationTable:
    n = len(rows)
    absolute_time_index = list(range(1, n + 1))
    return SimulationTable(
        pl.DataFrame(
            {
                "block": ["b1"] * n,
                "component": [r[0] for r in rows],
                "output": [r[1] for r in rows],
                "absolute_time_index": absolute_time_index,
                "block_time_index": absolute_time_index,
                "scenario_index": [r[2] for r in rows],
                "value": [r[4] for r in rows],
                "basis_status": ["ok"] * n,
            }
        ).lazy()
    )


def make_calendar(rows: list[tuple[str, str, int, datetime, float]]) -> Calendar:
    n = len(rows)
    return Calendar(
        id="calendar",
        dataframe=pl.DataFrame(
            {
                "absolute_time_index": list(range(1, n + 1)),
                "block": ["b1"] * n,
                "granular_date": [r[3] for r in rows],
            },
            schema_overrides={"granular_date": pl.Datetime},
        ).lazy(),
    )


def build_raw_input_data(
    system: Any,
    taxon_by_model: dict[str, str],
    view_config: ViewConfig,
    simulation_tables: list[SimulationTable],
    calendar: Calendar,
    catalogs: dict[str, Catalog] | None = None,
) -> RawInputData:
    """
    Build a real RawInputData, skipping only the disk-reading Loader.load() step:
    system/libraries/taxonomy are minimal but real objects, populated with just
    enough to drive the pipeline steps under test.
    """
    return RawInputData(
        taxonomy=Taxonomy(id="taxonomy"),
        libraries={
            "lib": Library(
                id="lib",
                description="",
                port_types=[],
                models={},
                models_by_taxonomy_category={},
                taxon_by_model=taxon_by_model,
            )
        },
        system=system,
        view_config=view_config,
        simulation_tables=simulation_tables,
        calendar=calendar,
        catalogs=catalogs or {},
    )
