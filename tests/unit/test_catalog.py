# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder import AggregOperatorType, Metric, PropertySchema, Term, load_catalog
from gems_views_builder.input.catalog import MetricData, TermData


def test_catalog_loads(test_dataset_dir: Path) -> None:
    catalog_path = sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0]
    catalog = load_catalog(catalog_path)
    assert isinstance(catalog.id, str)
    assert isinstance(catalog.taxonomy, str)
    assert isinstance(catalog.location_taxonomy_category, str)
    assert len(catalog.metrics) > 0


def test_catalog_metrics_are_typed(test_dataset_dir: Path) -> None:
    catalog_path = sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0]
    catalog = load_catalog(catalog_path)
    for metric in catalog.metrics.values():
        assert isinstance(metric, Metric)
        assert isinstance(metric.id, str)
        assert isinstance(metric.terms_operator, AggregOperatorType)
        assert isinstance(metric.time_operator, AggregOperatorType)
        assert len(metric.terms) > 0


def test_catalog_terms_are_typed(test_dataset_dir: Path) -> None:
    catalog_path = sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0]
    catalog = load_catalog(catalog_path)
    for metric in catalog.metrics.values():
        for term in metric.terms:
            assert isinstance(term, Term)
            assert isinstance(term.taxonomy_category, str)
            assert isinstance(term.output_id, str)
            assert term.location_port is None or isinstance(term.location_port, str)


def test_catalog_known_metrics(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    metric_ids = set(catalog.metrics.keys())
    assert "LOAD" in metric_ids


def test_metric_filter_property_requires_value() -> None:
    with pytest.raises(ValueError, match="metric filter property must include a value"):
        MetricData(
            id="X",
            terms=[],
            terms_operator=AggregOperatorType.SUM,
            time_operator=AggregOperatorType.SUM,
            filter=PropertySchema(key="technology"),
        )


def test_term_location_port_none_is_valid() -> None:
    term_data = TermData(taxonomy_category="production", output_id="p", location_port=None)
    assert term_data.location_port is None


def test_term_location_port_empty_string_is_rejected() -> None:
    with pytest.raises(ValueError, match="location-port must not be an empty or blank string"):
        TermData(taxonomy_category="production", output_id="p", location_port="")


def test_term_location_port_blank_string_is_rejected() -> None:
    with pytest.raises(ValueError, match="location-port must not be an empty or blank string"):
        TermData(taxonomy_category="production", output_id="p", location_port="   ")


def test_catalog_operators_valid_values(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    for metric in catalog.metrics.values():
        assert metric.terms_operator in (AggregOperatorType.SUM, AggregOperatorType.AVG)
        assert metric.time_operator in (AggregOperatorType.SUM, AggregOperatorType.AVG)
