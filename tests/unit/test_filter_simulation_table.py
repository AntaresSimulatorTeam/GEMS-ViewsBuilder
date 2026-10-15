# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import polars as pl
import pytest

from gems_views_builder import Calendar, FilteredSimulationTable
from gems_views_builder.input.simulation_table import SimulationTable, filter_simulation_table
from gems_views_builder.input.view_building_input_data import concat_simulation_tables
from tests.common import make_simulation_table_row


def make_calendar(absolute_time_index: int, block: str, granular_date: datetime) -> Calendar:
    return Calendar(
        id="calendar",
        dataframe=pl.DataFrame(
            {"absolute_time_index": [absolute_time_index], "block": [block], "granular_date": [granular_date]},
            schema_overrides={"granular_date": pl.Datetime},
        ).lazy(),
    )


def simulation_table(rows: list[dict[str, object]]) -> SimulationTable:
    return SimulationTable(
        pl.DataFrame(
            rows,
            schema_overrides={
                "absolute_time_index": pl.Int64,
                "block_time_index": pl.Int64,
                "scenario_index": pl.Int64,
                "value": pl.Float64,
            },
        ).lazy()
    )


def test_filter_simulation_table_keeps_calendar_matches_and_null_time_index() -> None:
    granular_date = datetime(2026, 1, 1)
    calendar = make_calendar(absolute_time_index=1, block="b1", granular_date=granular_date)
    table = simulation_table(
        [
            make_simulation_table_row(component="kept", absolute_time_index=1),
            make_simulation_table_row(component="other-time", absolute_time_index=99),
            make_simulation_table_row(component="static", absolute_time_index=None),
        ]
    )

    filtered_table = filter_simulation_table(table.dataframe, calendar)

    assert isinstance(filtered_table, FilteredSimulationTable)
    assert filtered_table.file_path.exists()
    filtered = pl.read_parquet(filtered_table.file_path).sort("component")
    assert filtered["component"].to_list() == ["kept", "static"]
    kept = filtered.filter(pl.col("component") == "kept")
    assert kept["granular_date"][0] == granular_date
    assert filtered.filter(pl.col("component") == "static")["granular_date"][0] is None


def test_filter_simulation_table_drops_mismatched_block() -> None:
    """
    Inner join on absolute_time_index
    Static will be in filtered table with null date because absolute_time_index is null(we want to keep them)
    """
    calendar = make_calendar(absolute_time_index=1, block="b1", granular_date=datetime(2026, 1, 1))
    table = simulation_table(
        [
            make_simulation_table_row(component="kept", block="b1", absolute_time_index=1),
            make_simulation_table_row(component="wrong-block", block="b2", absolute_time_index=1),
            make_simulation_table_row(component="static", absolute_time_index=None, block="b2"),
        ]
    )

    filtered_table = filter_simulation_table(table.dataframe, calendar)
    filtered = pl.read_parquet(filtered_table.file_path)

    assert set(filtered["component"].to_list()) == {"kept", "static"}
    assert filtered.filter(pl.col("component") == "static")["block"][0] == "b2"
    assert filtered.filter(pl.col("component") == "kept")["block"][0] == "b1"


@pytest.mark.parametrize(
    ("block_a", "block_b", "expected_components"),
    [
        ("b1", "b1", {"comp-a", "comp-b"}),
        ("b1", "b2", {"comp-a"}),
        ("b2", "b1", {"comp-b"}),
    ],
)
def test_filter_simulation_table_keeps_calendar_matching_rows_from_every_table(
    block_a: str,
    block_b: str,
    expected_components: set[str],
) -> None:
    granular_date = datetime(2026, 1, 1)
    calendar = make_calendar(absolute_time_index=1, block="b1", granular_date=granular_date)
    st_a = SimulationTable(
        pl.DataFrame([make_simulation_table_row(component="comp-a", block=block_a, absolute_time_index=1)]).lazy()
    )
    st_b = SimulationTable(
        pl.DataFrame([make_simulation_table_row(component="comp-b", block=block_b, absolute_time_index=1)]).lazy()
    )

    filtered_table = filter_simulation_table(concat_simulation_tables([st_a, st_b]), calendar)

    filtered = pl.read_parquet(filtered_table.file_path)
    assert set(filtered["component"].to_list()) == expected_components
