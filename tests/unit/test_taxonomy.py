# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder import TaxonomyCategory, TaxonomyItem, load_taxonomy

TAXONOMY_YML = """
taxonomy:
  id: my_taxonomy
  description: Minimal taxonomy
  categories:
    - id: production
      ports:
        - id: p_port
      variables:
        - id: p
"""


def test_load_taxonomy_reads_category_port_and_variable(tmp_path: Path) -> None:
    taxonomy_path = tmp_path / "taxonomy.yml"
    taxonomy_path.write_text(TAXONOMY_YML)

    taxonomy = load_taxonomy(taxonomy_path)

    assert taxonomy.id == "my_taxonomy"
    assert taxonomy.description == "Minimal taxonomy"
    category = taxonomy.categories["production"]
    assert isinstance(category, TaxonomyCategory)
    assert category.id == "production"
    assert category.ports == [TaxonomyItem(id="p_port")]
    assert category.variables == [TaxonomyItem(id="p")]


def test_load_taxonomy_raises_when_root_key_is_missing(tmp_path: Path) -> None:
    taxonomy_path = tmp_path / "taxonomy.yml"
    taxonomy_path.write_text("id: broken\n")

    with pytest.raises(ValueError, match="taxonomy"):
        load_taxonomy(taxonomy_path)
