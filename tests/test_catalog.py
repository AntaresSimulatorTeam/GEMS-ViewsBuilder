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

from pathlib import Path

import pytest

from gems_views_builder import Metric, Term, TermsOperator, TimeOperator, load_catalog
from gems_views_builder.catalog import MetricData, PropertySchema


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
        assert isinstance(metric.terms_operator, TermsOperator)
        assert isinstance(metric.time_operator, TimeOperator)
        assert len(metric.terms) > 0


def test_catalog_terms_are_typed(test_dataset_dir: Path) -> None:
    catalog_path = sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0]
    catalog = load_catalog(catalog_path)
    for metric in catalog.metrics.values():
        for term in metric.terms:
            assert isinstance(term, Term)
            assert isinstance(term.taxonomy_category, str)
            assert isinstance(term.output_id, str)
            assert term.location_ports is None or isinstance(term.location_ports, (str, tuple))


def test_catalog_known_metrics(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    metric_ids = set(catalog.metrics.keys())
    assert "LOAD" in metric_ids


def test_metric_filter_property_requires_value() -> None:
    with pytest.raises(ValueError, match="metric filter property must include a value"):
        MetricData(
            id="X",
            terms=[],
            terms_operator=TermsOperator.SUM,
            time_operator=TimeOperator.SUM,
            filter=PropertySchema(key="technology"),
        )


def test_catalog_operators_valid_values(test_dataset_dir: Path) -> None:
    catalog = load_catalog(sorted((test_dataset_dir / "catalogs").glob("*.yml"))[0])
    for metric in catalog.metrics.values():
        assert metric.terms_operator in (TermsOperator.SUM, TermsOperator.AVG)
        assert metric.time_operator in (TimeOperator.SUM, TimeOperator.AVG)
