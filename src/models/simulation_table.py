from dataclasses import dataclass

import polars as pl


@dataclass
class SimulationTable:
    """Table of simulation data"""

    id: str
    simulation_table_dataframe: pl.DataFrame
