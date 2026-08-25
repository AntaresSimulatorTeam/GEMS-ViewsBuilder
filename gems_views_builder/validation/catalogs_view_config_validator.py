# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
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
        view_config_metric_ids_by_catalog = self.view_config.group_metrics_by_catalog()
        for catalog in self.catalogs:
            self._validate_catalog_against_view_config(catalog, view_config_metric_ids_by_catalog)
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
        self, catalog: Catalog, view_config_metric_ids_by_catalog: dict[str, set[str]]
    ) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against view config {self.view_config.id!r}")
        self._match_taxonomy(catalog)
        self._match_location_taxonomy_category(catalog)
        validate_used_metric_ids(catalog, view_config_metric_ids_by_catalog, self.view_config.id)


def validate_used_metric_ids(
    catalog: Catalog, view_config_metric_ids_by_catalog: dict[str, set[str]], view_config_id: str
) -> None:
    used_metric_ids_by_catalog = view_config_metric_ids_by_catalog.get(catalog.id, set())
    for metric_id in used_metric_ids_by_catalog:
        if metric_id not in catalog.metrics:
            raise ValueError(
                f"View config {view_config_id!r} metric "
                f"{f'{catalog.id}.{metric_id}'!r} is not defined in catalog {catalog.id!r}"
            )
