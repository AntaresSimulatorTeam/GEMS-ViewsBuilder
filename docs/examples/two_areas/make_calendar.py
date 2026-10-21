# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Build calendar.csv from the time steps and blocks of a SimulationTable."""

import polars as pl

st = pl.read_csv("simulation-tables/st-mc-0.csv")
calendar = (
    st.filter(pl.col("absolute_time_index").is_not_null())
    .select("absolute_time_index", "block")
    .unique()
    .sort("absolute_time_index")
    .with_columns(
        granular_date=(pl.datetime(2030, 1, 25) + pl.duration(hours=pl.col("absolute_time_index")))
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
)
calendar.write_csv("calendar.csv")
