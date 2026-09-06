# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import polars as pl
import pytest

from gems_views_builder.spatial_filter import SpatialFilter


def make_dataframe(location_values: list[tuple[str, float]]) -> pl.LazyFrame:
    return pl.DataFrame(
        {
            "metric_location": [location for location, _ in location_values],
            "metric_value": [value for _, value in location_values],
        }
    ).lazy()


@pytest.mark.parametrize(
    ("spatial_filter", "expected_locations"),
    [
        (["busA"], {"busA"}),
        (["busA", "busC"], {"busA", "busC"}),
        (None, {"busA", "busB", "busC"}),
    ],
)
def test_spatial_filter(spatial_filter: list[str] | None, expected_locations: set[str]) -> None:
    # Arrange
    dataframe = make_dataframe([("busA", 100.0), ("busB", 50.0), ("busC", 999.0)])

    # Act
    result = SpatialFilter(spatial_filter).apply_spatial_filter(dataframe)

    # Assert
    assert set(result.collect()["metric_location"].to_list()) == expected_locations
    assert set(dataframe.collect()["metric_location"].to_list()) == {"busA", "busB", "busC"}
