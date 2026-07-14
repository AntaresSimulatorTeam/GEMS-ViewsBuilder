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
        # # More checks

    def _match_taxonomy_id(self) -> None:
        if self.taxonomy.id != self.view_config.taxonomy_id:
            raise ValueError(
                f"View config {self.view_config.id!r} references taxonomy {self.view_config.taxonomy_id!r}, "
                f"but study taxonomy id is {self.taxonomy.id!r}"
            )

    def _validate_location_taxonomy_category(self) -> None:
        categories = self.taxonomy.get_taxonomy_categories()
        if self.view_config.scope_taxon_category not in set(categories.keys()):
            raise ValueError(
                f"View config {self.view_config.id!r} scope location taxonomy category "
                f"{self.view_config.scope_taxon_category!r} is not a category of taxonomy {self.taxonomy.id!r}"
            )
