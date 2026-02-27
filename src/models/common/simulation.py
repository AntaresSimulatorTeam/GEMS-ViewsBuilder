from dataclasses import dataclass

import polars as pl


@dataclass
class Simulation:
    id: str
    simulation_dataframe: pl.DataFrame
