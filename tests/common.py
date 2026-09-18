# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

SIMULATION_TABLE_ROW: dict[str, object] = {
    "block": "b1",
    "component": "comp",
    "output": "out",
    "absolute_time_index": 1,
    "block_time_index": 1,
    "scenario_index": 1,
    "value": 1.0,
    "basis_status": "ok",
}


def make_simulation_table_row(**overrides: object) -> dict[str, object]:
    return {**SIMULATION_TABLE_ROW, **overrides}
