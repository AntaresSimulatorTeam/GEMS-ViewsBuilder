# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

import polars as pl
from pytest import approx

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.metric_view import MetricView


def temporal_metric_view(tmp_path: Path, values_by_scenario: dict[int, float]) -> MetricView:
    """Temporal aggregation-shaped parquet (input to scenario aggregation)."""
    scenarios = sorted(values_by_scenario)
    n = len(scenarios)
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * n,
            "metric_location": ["L"] * n,
            "breakdown_properties": [""] * n,
            "view_date": [datetime(2026, 1, 1)] * n,
            "scenario_id": scenarios,
            "metric_value": [values_by_scenario[s] for s in scenarios],
        },
        schema_overrides={"view_date": pl.Datetime, "scenario_id": pl.Int64},
    )
    path = tmp_path / "temporal.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


def test_scenario_aggregation_false_preserves_rows_and_adds_columns(tmp_path: Path) -> None:
    # Arrange
    values = {0: 10.0, 1: 20.0, 2: 30.0}
    metric_view = temporal_metric_view(tmp_path, values_by_scenario=values)
    original_path = metric_view.persistence_path
    aggregator = ScenarioAggregator(False)

    # Act
    aggregator.run(metric_view)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path).sort("scenario_id")
    assert metric_view.persistence_path == original_path
    assert metric_view.persistence_path.name == original_path.name
    assert "scenario_aggregation" in df.columns and "scenario_stat" in df.columns
    assert df.height == 3
    assert df["scenario_aggregation"].to_list() == [False, False, False]
    assert df["scenario_stat"].null_count() == 3
    assert df["scenario_id"].to_list() == [0, 1, 2]
    assert df["metric_value"].to_list() == [approx(10.0), approx(20.0), approx(30.0)]


def test_scenario_aggregation_true_emits_exp_std_min_max(tmp_path: Path) -> None:
    # Arrange
    values = {0: 10.0, 1: 20.0, 2: 30.0}
    metric_view = temporal_metric_view(tmp_path, values_by_scenario=values)
    original_path = metric_view.persistence_path
    aggregator = ScenarioAggregator(True)
    expected_values = list(values.values())

    # Act
    aggregator.run(metric_view)

    # Assert
    df = pl.read_parquet(metric_view.persistence_path)
    assert metric_view.persistence_path == original_path
    assert df.height == 4
    assert set(df["scenario_stat"].to_list()) == {"exp", "std", "min", "max"}
    assert df["scenario_aggregation"].to_list() == [True] * 4
    assert df["scenario_id"].null_count() == 4

    by_stat = {row["scenario_stat"]: row["metric_value"] for row in df.iter_rows(named=True)}
    assert by_stat["exp"] == approx(mean(expected_values))
    assert by_stat["std"] == approx(pstdev(expected_values))
    assert by_stat["min"] == approx(min(expected_values))
    assert by_stat["max"] == approx(max(expected_values))
