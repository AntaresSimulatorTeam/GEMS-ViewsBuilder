# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

import polars as pl

from gems_views_builder.common import BUCKET_COUNT, murmur_hash
from gems_views_builder.input.catalog import AggregOperatorType, Metric, Term
from gems_views_builder.input.component import Component
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_structure_table import MetricStructureTable, get_unique_pair_lookup_rows
from gems_views_builder.metrics_structure_builder import build_metric_structure_tables


def make_component(component_id: str, taxonomy_category: str) -> Component:
    component = Component(SimpleNamespace(id=component_id, taxonomy_category=taxonomy_category))
    return component


def make_metric(metric_id: str, taxonomy_category: str, output_id: str) -> Metric:
    return Metric(
        id=metric_id,
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
        terms=[Term(taxonomy_category=taxonomy_category, output_id=output_id, location_port=None)],
    )


def make_view_config(view_config_id: str, location_taxonomy_category: str, metrics: list[Metric]) -> ViewConfig:
    return ViewConfig(
        id=view_config_id,
        location_taxonomy_category=location_taxonomy_category,
        taxonomy_id="taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
        metrics=metrics,
    )


def structure_row(component: str, output: str) -> dict[str, object]:
    pair_id = murmur_hash(component, output)
    return {
        "component": component,
        "output": output,
        "pair_id": pair_id,
        "bucket_id": pair_id % BUCKET_COUNT,
    }


# murmur_hash("component_1", "output_1") == -4265748115851316547, bucket 61
# murmur_hash("component_2", "output_2") == -3209794214191856216, bucket 40
EXPECTED_PAIR_LOOKUP = pl.DataFrame(
    [
        {
            "component": "component_1",
            "output": "output_1",
            "pair_id": -4265748115851316547,
            "bucket_id": 61,
        },
        {
            "component": "component_2",
            "output": "output_2",
            "pair_id": -3209794214191856216,
            "bucket_id": 40,
        },
    ],
)


def test_get_pair_lookup_rows() -> None:
    # Arrange
    ms_table = MetricStructureTable(
        rows=[
            structure_row("component_1", "output_1"),
            structure_row("component_2", "output_2"),
            structure_row("component_1", "output_1"),
        ],
        metric_id="metric_1",
    )

    # Act
    pair_lookup_rows = ms_table.get_pair_lookup_rows().sort("component", "output")

    # Assert
    assert pair_lookup_rows.equals(EXPECTED_PAIR_LOOKUP)


def test_build_metric_structure_tables() -> None:
    metric_a1 = make_metric("metric_a1", taxonomy_category="generators", output_id="p")
    metric_a2 = make_metric("metric_a2", taxonomy_category="loads", output_id="load")
    metric_b1 = make_metric("metric_b1", taxonomy_category="generators", output_id="p")

    view_config_a = make_view_config("view_a", location_taxonomy_category="generators", metrics=[metric_a1, metric_b1])
    view_config_b = make_view_config("view_b", location_taxonomy_category="loads", metrics=[metric_a2])

    components_by_taxon = {
        "generators": [make_component("gen_1", "generators"), make_component("gen_2", "generators")],
        "loads": [make_component("load_1", "loads")],
    }

    # Act
    metric_structure_tables = build_metric_structure_tables(
        [view_config_a, view_config_b],
        components_by_taxon,
    )

    assert set(metric_structure_tables) == {
        "view_a_metric_a1",
        "view_a_metric_b1",
        "view_b_metric_a2",
    }
    assert all(isinstance(table, MetricStructureTable) for table in metric_structure_tables.values())


def test_get_unique_pair_lookup_rows() -> None:
    # Arrange
    ms_table_by_view_config_metrics = {
        "view_config_1_metric_1": MetricStructureTable(
            rows=[
                structure_row("component_1", "output_1"),
                structure_row("component_1", "output_1"),
            ],
            metric_id="metric_1",
        ),
        "view_config_1_metric_2": MetricStructureTable(
            rows=[
                structure_row("component_2", "output_2"),
                structure_row("component_2", "output_2"),
                structure_row("component_1", "output_1"),
            ],
            metric_id="metric_2",
        ),
    }

    # Act
    pair_lookup_rows = get_unique_pair_lookup_rows(ms_table_by_view_config_metrics).sort("component", "output")

    # Assert
    assert pair_lookup_rows.equals(EXPECTED_PAIR_LOOKUP)
