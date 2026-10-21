# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Check the hourly View of the two-area example: energy balance and country total."""

import polars as pl

hourly = pl.read_parquet("views/areas_hourly_*.parquet").pivot(
    on="metric_id", index=["metric_location", "view_date", "scenario_id"], values="metric_value"
)

# 1. Energy balance of each area and of the country, at every hour
balance = hourly.select(
    (pl.col("GENERATION") + pl.col("NET_IMPORT") + pl.col("UNSUPPLIED_ENERGY")
     - pl.col("SPILLED_ENERGY") - pl.col("LOAD")).abs().max()
).item()

# 2. The country total equals the sum of the two areas
areas = (
    hourly.filter(pl.col("metric_location") != "country_1")
    .group_by("view_date", "scenario_id")
    .agg(pl.col("LOAD", "GENERATION", "NET_IMPORT", "UNSUPPLIED_ENERGY").sum())
)
country = hourly.filter(pl.col("metric_location") == "country_1").join(
    areas, on=["view_date", "scenario_id"], suffix="_areas"
)
gap = country.select(
    (pl.col(m) - pl.col(f"{m}_areas")).abs().max().alias(m)
    for m in ["LOAD", "GENERATION", "NET_IMPORT", "UNSUPPLIED_ENERGY"]
)
print(f"largest balance gap: {balance:.1e}")
print(gap)
