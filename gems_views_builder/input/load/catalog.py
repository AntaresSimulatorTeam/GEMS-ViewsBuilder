# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import yaml

from gems_views_builder.input.catalog import Catalog, CatalogData, Metric, MetricData, Term, TermData


def to_term(term_data: TermData) -> Term:
    return Term(
        taxonomy_category=term_data.taxonomy_category,
        output_id=term_data.output_id,
        location_port=term_data.location_port,
        weight_output_id=term_data.weight_output_id,
    )


def to_metric(metric_data: MetricData) -> Metric:
    return Metric(
        id=metric_data.id,
        terms=[to_term(term) for term in metric_data.terms],
        terms_operator=metric_data.terms_operator,
        time_operator=metric_data.time_operator,
        breakdown=list(metric_data.breakdown) if metric_data.breakdown else None,
        filter=metric_data.filter,
    )


def load_catalogs(catalogs_dir: Path, catalog_ids: set[str]) -> dict[str, Catalog]:
    catalogs: dict[str, Catalog] = {}
    for catalog_id in catalog_ids:
        catalogs[catalog_id] = load_catalog(catalogs_dir / f"{catalog_id}.yml")
    return catalogs


def load_catalog(catalog_file_path: Path) -> Catalog:
    logging.info(f"Loading catalog from {catalog_file_path}")
    parsed_catalog = load_catalog_file(catalog_file_path)
    catalog = Catalog(
        id=parsed_catalog.id,
        taxonomy=parsed_catalog.taxonomy,
        location_taxonomy_category=parsed_catalog.location.taxonomy_category,
        metrics={metric.id: to_metric(metric) for metric in parsed_catalog.metrics_definition},
    )
    logging.info(
        f"Catalog {catalog.id!r} loaded with taxonomy {catalog.taxonomy!r} and {len(catalog.metrics)} metric(s)"
    )
    return catalog


def load_catalog_file(catalog_file_path: Path) -> CatalogData:
    logging.debug(f"Loading catalog YAML from {catalog_file_path}")
    if not catalog_file_path.exists():
        raise FileNotFoundError(f"Catalog file {catalog_file_path} not found")
    with open(catalog_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "catalog" not in raw:
        raise ValueError(f"catalog.yml file {catalog_file_path} is missing the 'catalog' key at the root")
    return CatalogData.model_validate(raw["catalog"])
