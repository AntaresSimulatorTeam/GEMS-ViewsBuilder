# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import yaml

from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyData


def load_taxonomy(taxonomy_file_path: Path) -> Taxonomy:
    logging.info(f"Loading taxonomy from {taxonomy_file_path}")
    parsed = load_taxonomy_file(taxonomy_file_path)
    taxonomy = Taxonomy(
        id=parsed.id,
        description=parsed.description,
        categories=parsed.categories,
    )
    logging.info(f"Taxonomy {taxonomy.id!r} loaded with {len(taxonomy.categories)} categor(ies)")
    return taxonomy


def load_taxonomy_file(taxonomy_file_path: Path) -> TaxonomyData:
    logging.debug(f"Loading taxonomy YAML from {taxonomy_file_path}")
    with open(taxonomy_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "taxonomy" not in raw:
        raise ValueError(f"taxonomy.yml file {taxonomy_file_path} is missing the 'taxonomy' key at the root")
    logging.debug(f"Taxonomy YAML parsed successfully from {taxonomy_file_path}")
    return TaxonomyData.model_validate(raw["taxonomy"])
