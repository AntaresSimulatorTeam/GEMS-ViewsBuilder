# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from gems_views_builder.aggregators.parallel import SerialExecutor, get_executor
from gems_views_builder.aggregators.pattern_aggregator import AggregationPatternList, shared_location_filter
from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView

LOCATIONS = ["busA", "busB", "busC"]


def make_pattern(
    pattern_id: str, granularity: TimeGranularity, scenario: bool, locations: list[str] | None = None
) -> AggregationPattern:
    return AggregationPattern(id=pattern_id, time_granularity=granularity, scenario=scenario, location_filter=locations)


PATTERNS = (
    make_pattern("hour_all", TimeGranularity.HOUR, True, ["busA", "busB"]),
    make_pattern("hour_per", TimeGranularity.HOUR, False, ["busB"]),
    make_pattern("day_all", TimeGranularity.DAY, True),
    make_pattern("day_per", TimeGranularity.DAY, False, ["busC"]),
    make_pattern("month_all", TimeGranularity.MONTH, True),
)


def make_view_config(patterns: tuple[AggregationPattern, ...]) -> ViewConfig:
    return ViewConfig(id="view", location_taxonomy_category="balance", taxonomy_id="t", aggregation_patterns=patterns)


def make_metric_view(tmp_path: Path) -> MetricView:
    """Terms-aggregated view: 3 locations x 3 scenarios x 48 hours."""
    rows = [
        (location, scenario, hour, float(10 * i + scenario + hour))
        for i, location in enumerate(LOCATIONS)
        for scenario in range(3)
        for hour in range(48)
    ]
    dataframe = pl.DataFrame(
        {
            "metric_id": ["M"] * len(rows),
            "metric_location": [row[0] for row in rows],
            "breakdown_properties": [""] * len(rows),
            "absolute_time_index": [row[2] for row in rows],
            "scenario_id": [row[1] for row in rows],
            "granular_metric_value": [row[3] for row in rows],
            "granular_date": [datetime(2026, 1, 1) + timedelta(hours=row[2]) for row in rows],
        },
        schema_overrides={"granular_date": pl.Datetime},
    )
    path = tmp_path / "granular.parquet"
    dataframe.write_parquet(path)
    return MetricView(path)


METRIC = Metric(id="M", terms=[], terms_operator=AggregOperatorType.SUM, time_operator=AggregOperatorType.SUM)


@pytest.fixture
def workers(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[int]:
    monkeypatch.setenv("GVB_MAX_WORKERS", str(request.param))
    get_executor.cache_clear()
    yield request.param
    get_executor().shutdown()
    get_executor.cache_clear()


def test_shared_location_filter_is_union_when_every_pattern_filters() -> None:
    patterns = [
        make_pattern("a", TimeGranularity.DAY, True, ["x", "y"]),
        make_pattern("b", TimeGranularity.DAY, False, ["z", "x"]),
    ]
    assert shared_location_filter(patterns) == ["x", "y", "z"]


def test_shared_location_filter_is_none_when_one_pattern_keeps_all_locations() -> None:
    patterns = [make_pattern("a", TimeGranularity.DAY, True, ["x"]), make_pattern("b", TimeGranularity.DAY, False)]
    assert shared_location_filter(patterns) is None


def test_one_worker_uses_serial_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GVB_MAX_WORKERS", "1")
    get_executor.cache_clear()
    assert isinstance(get_executor(), SerialExecutor)
    get_executor.cache_clear()


@pytest.mark.parametrize("workers", [1, 4], indirect=True)
def test_patterns_match_one_pattern_at_a_time(tmp_path: Path, workers: int) -> None:
    # Arrange
    metric_view = make_metric_view(tmp_path)

    # Act
    views = AggregationPatternList(make_view_config(PATTERNS)).run(metric_view, METRIC)

    # Assert: same output, in the same order, as time- then scenario-aggregating each pattern alone
    assert [view.aggregation_pattern_id for view in views] == [pattern.id for pattern in PATTERNS]
    for pattern, view in zip(PATTERNS, views, strict=True):
        time_view = TimeAggregator(pattern.time_granularity).run(metric_view, METRIC)
        # Keep a reference: a TemporalMetricView deletes its file when garbage-collected.
        expected_view = ScenarioAggregator(pattern).run(time_view)
        expected = pl.read_parquet(expected_view.persistence_path)
        actual = pl.read_parquet(view.persistence_path)
        sort_columns = ["metric_location", "view_date", "scenario_id", "scenario_stat"]
        assert_frame_equal(actual.sort(sort_columns), expected.sort(sort_columns))
        if pattern.location_filter:
            assert set(actual["metric_location"]) == set(pattern.location_filter)


@pytest.mark.parametrize("workers", [4], indirect=True)
def test_time_aggregated_intermediates_are_removed(tmp_path: Path, workers: int) -> None:
    pattern_list = AggregationPatternList(make_view_config(PATTERNS))
    views = pattern_list.run(make_metric_view(tmp_path), METRIC)
    assert sorted(pattern_list._root_dir.iterdir()) == sorted(view.persistence_path for view in views)
