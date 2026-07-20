from pathlib import Path

import pytest

from gems_views_builder import Metric, PropertySchema, Term, TermsOperator, TimeOperator, load_catalog
from gems_views_builder.input.catalog import MetricData, TermData


def test_catalog_loads(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    assert isinstance(catalog.id, str)
    assert isinstance(catalog.taxonomy, str)
    assert isinstance(catalog.location_taxonomy_category, str)
    assert catalog.metrics


def test_catalog_metrics_and_terms_are_typed(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    for metric in catalog.metrics.values():
        assert isinstance(metric, Metric)
        assert isinstance(metric.terms_operator, TermsOperator)
        assert isinstance(metric.time_operator, TimeOperator)
        for term in metric.terms:
            assert isinstance(term, Term)
            assert isinstance(term.location_port, str | type(None))


def test_metric_filter_property_requires_value() -> None:
    with pytest.raises(ValueError, match="metric filter property must include a value"):
        MetricData(
            id="X",
            terms=[],
            terms_operator=TermsOperator.SUM,
            time_operator=TimeOperator.SUM,
            filter=PropertySchema(key="technology"),
        )


def test_term_location_port_validation() -> None:
    assert TermData(taxonomy_category="production", output_id="p", location_port=None).location_port is None
    for value in ("", "   "):
        with pytest.raises(ValueError, match="location-port must not be an empty or blank string"):
            TermData(taxonomy_category="production", output_id="p", location_port=value)
