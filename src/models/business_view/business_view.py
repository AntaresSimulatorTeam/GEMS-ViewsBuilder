from dataclasses import dataclass

import polars as pl


@dataclass
class BusinessView:
    business_view_dataframe: pl.DataFrame
