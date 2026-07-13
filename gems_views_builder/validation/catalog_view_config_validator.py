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

"""Validate consistency between loaded catalogs and the view config."""

import logging
from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.view_config import ViewConfig


@dataclass
class CatalogsViewConfigValidator:
    catalogs: list[Catalog]
    view_config: ViewConfig

    def validate(self) -> None:
        logging.info(f"Validating {len(self.catalogs)} catalog(s) against view config {self.view_config.id!r}")
        for catalog in self.catalogs:
            self._validate_catalog_against_view_config(catalog)
        logging.info(f"All catalogs are consistent with view config {self.view_config.id!r}")

    def _validate_catalog_against_view_config(self, catalog: Catalog) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against view config {self.view_config.id!r}")
        if catalog.taxonomy != self.view_config.taxonomy_id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, "
                f"but view config {self.view_config.id!r} references taxonomy "
                f"{self.view_config.taxonomy_id!r}"
            )
        if catalog.location_taxonomy_category != self.view_config.location_taxonomy_category:
            raise ValueError(
                f"Catalog {catalog.id!r} location taxonomy category "
                f"{catalog.location_taxonomy_category!r} does not match view config "
                f"{self.view_config.id!r} location taxonomy category "
                f"{self.view_config.location_taxonomy_category!r}"
            )
