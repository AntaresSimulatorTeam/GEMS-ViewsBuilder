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
class CatalogViewConfigValidator:
    catalog: Catalog
    view_config: ViewConfig

    def validate(self) -> None:
        logging.info(f"Validating catalog {self.catalog.id!r} against view config {self.view_config.id!r}")
        if self.catalog.taxonomy != self.view_config.taxonomy_id:
            raise ValueError(
                f"Catalog {self.catalog.id!r} references taxonomy {self.catalog.taxonomy!r}, "
                f"but view config {self.view_config.id!r} references taxonomy "
                f"{self.view_config.taxonomy_id!r}"
            )
        if self.catalog.location_taxonomy_category != self.view_config.location_taxonomy_category:
            raise ValueError(
                f"Catalog {self.catalog.id!r} location taxonomy category "
                f"{self.catalog.location_taxonomy_category!r} does not match view config "
                f"{self.view_config.id!r} location taxonomy category "
                f"{self.view_config.location_taxonomy_category!r}"
            )


def validate_catalogs_against_view_config(catalogs: dict[str, Catalog], view_config: ViewConfig) -> None:
    logging.info(f"Validating {len(catalogs)} catalog(s) against view config {view_config.id!r}")
    for catalog in catalogs.values():
        CatalogViewConfigValidator(catalog, view_config).validate()
    logging.info(f"All catalogs are consistent with view config {view_config.id!r}")
