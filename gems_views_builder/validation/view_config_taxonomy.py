# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Validate consistency between the view config and the study taxonomy."""

from dataclasses import dataclass

from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


@dataclass
class ViewConfigTaxonomyValidator:
    taxonomy: Taxonomy
    view_config: ViewConfig

    def validate(self) -> None:
        self._match_taxonomy_id()
        self._validate_location_taxonomy_category()

    def _match_taxonomy_id(self) -> None:
        if self.taxonomy.id != self.view_config.taxonomy_id:
            raise ValueError(
                f"View config {self.view_config.id!r} references taxonomy {self.view_config.taxonomy_id!r}, "
                f"but study taxonomy id is {self.taxonomy.id!r}"
            )

    def _validate_location_taxonomy_category(self) -> None:
        if self.view_config.location_taxonomy_category not in self.taxonomy.categories:
            raise ValueError(
                f"View config {self.view_config.id!r} scope location taxonomy category "
                f"{self.view_config.location_taxonomy_category!r} is not a category of taxonomy {self.taxonomy.id!r}"
            )
