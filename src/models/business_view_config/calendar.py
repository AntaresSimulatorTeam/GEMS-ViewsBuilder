from dataclasses import dataclass
from datetime import datetime

import polars as pl


@dataclass
class Calendar:
    """
    1st col: absolute_time_index
    2nd col: block
    3rd col: granular_date
    """

    id: str
    calendar_dataframe: pl.DataFrame

    def abs_time_index_to_block(self, abs_time_index: int) -> int:
        raise NotImplementedError()

    def abs_time_index_to_date(self, abs_time_index: int) -> datetime:
        raise NotImplementedError()
