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

from src import Catalog, Metric, Term, TermsOperator, TimeOperator

TEST_FILES_ROOT = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files"

CATALOG_PATH = [
    TEST_FILES_ROOT / "input_one_daily" / "catalogs" / "catalog_1.yml",
]


@pytest.mark.parametrize("catalog_path", CATALOG_PATH)
def test_catalog_loads(catalog_path: Path) -> None:
    catalog = Catalog(catalog_path)
    assert isinstance(catalog.id, str)
    assert isinstance(catalog.taxonomy, str)
    assert isinstance(catalog.location_taxonomy_category, str)
    assert len(catalog.metrics) > 0


@pytest.mark.parametrize("catalog_path", CATALOG_PATH)
def test_catalog_metrics_are_typed(catalog_path: Path) -> None:
    catalog = Catalog(catalog_path)
    for metric in catalog.metrics.values():
        assert isinstance(metric, Metric)
        assert isinstance(metric.id, str)
        assert isinstance(metric.terms_operator, TermsOperator)
        assert isinstance(metric.time_operator, TimeOperator)
        assert len(metric.terms) > 0


@pytest.mark.parametrize("catalog_path", CATALOG_PATH)
def test_catalog_terms_are_typed(catalog_path: Path) -> None:
    catalog = Catalog(catalog_path)
    for metric in catalog.metrics.values():
        for term in metric.terms:
            assert isinstance(term, Term)
            assert isinstance(term.taxonomy_category, str)
            assert isinstance(term.output_id, str)
            assert term.location_ports is None or isinstance(term.location_ports, str)


def test_catalog_known_metrics() -> None:
    catalog = Catalog(TEST_FILES_ROOT / "input_one_daily" / "catalogs" / "catalog_1.yml")
    metric_ids = set(catalog.metrics.keys())
    assert "OVERALL_COST" in metric_ids
    assert "MRG_PRICE" in metric_ids
    assert "UNSP_ENRG" in metric_ids


def test_catalog_operators_valid_values() -> None:
    catalog = Catalog(TEST_FILES_ROOT / "input_one_daily" / "catalogs" / "catalog_1.yml")
    for metric in catalog.metrics.values():
        assert metric.terms_operator in (TermsOperator.SUM, TermsOperator.AVG)
        assert metric.time_operator in (TimeOperator.SUM, TimeOperator.AVG)
