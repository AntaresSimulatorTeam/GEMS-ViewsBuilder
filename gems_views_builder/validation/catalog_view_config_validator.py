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
        metric_ids_by_catalog = self.view_config.group_metrics_by_catalog()
        seen_metric_id: set[str] = set()
        for catalog in self.catalogs:
            self._validate_catalog_against_view_config(
                catalog, seen_metric_id, metric_ids_by_catalog.get(catalog.id, set())
            )
        logging.info(f"All catalogs are consistent with view config {self.view_config.id!r}")

    def _match_taxonomy(self, catalog: Catalog) -> None:
        if catalog.taxonomy != self.view_config.taxonomy_id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, "
                f"but view config {self.view_config.id!r} references taxonomy "
                f"{self.view_config.taxonomy_id!r}"
            )

    def _match_location_taxonomy_category(self, catalog: Catalog) -> None:
        if catalog.location_taxonomy_category != self.view_config.location_taxonomy_category:
            raise ValueError(
                f"Catalog {catalog.id!r} location taxonomy category "
                f"{catalog.location_taxonomy_category!r} does not match view config "
                f"{self.view_config.id!r} location taxonomy category "
                f"{self.view_config.location_taxonomy_category!r}"
            )

    def _validate_catalog_against_view_config(
        self, catalog: Catalog, seen_metric_id: set[str], expected_metric_ids: set[str]
    ) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against view config {self.view_config.id!r}")
        self._match_taxonomy(catalog)
        self._match_location_taxonomy_category(catalog)

        for metric_id in expected_metric_ids:
            if metric_id not in catalog.metrics:
                raise ValueError(
                    f"View config {self.view_config.id!r} metric "
                    f"{f'{catalog.id}.{metric_id}'!r} is not defined in catalog {catalog.id!r}"
                )

        for metric_id in catalog.metrics:
            if metric_id in seen_metric_id:
                raise ValueError(f"Same metric id {metric_id!r} is defined in multiple catalogs!")
            seen_metric_id.add(metric_id)
