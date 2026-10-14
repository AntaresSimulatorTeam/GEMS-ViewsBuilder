# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder import AggregOperatorType, Metric, PropertySchema, Term, load_catalog
from gems_views_builder.input.catalog import MetricData, TermData

CATALOG_YML = """
catalog:
  id: catalog
  taxonomy: my_taxonomy
  location:
    taxonomy-category: balance
  metrics-definition:
    - id: LOAD
      terms:
        - taxonomy-category: consumption
          output-id: active_load
          location-port: p_port
      terms-operator: sum
      time-operator: sum
"""


def test_load_catalog_reads_one_metric(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.yml"
    catalog_path.write_text(CATALOG_YML)

    catalog = load_catalog(catalog_path)

    assert catalog.id == "catalog"
    assert catalog.taxonomy == "my_taxonomy"
    assert catalog.location_taxonomy_category == "balance"
    metric = catalog.metrics["LOAD"]
    assert isinstance(metric, Metric)
    assert metric.terms_operator is AggregOperatorType.SUM
    assert metric.time_operator is AggregOperatorType.SUM
    assert metric.terms == [Term(taxonomy_category="consumption", output_id="active_load", location_port="p_port")]


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
