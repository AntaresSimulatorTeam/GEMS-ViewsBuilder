# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.view_config import ViewConfig


class ViewConfigMetricsAgainstCatalogsValidator:
    def __init__(self, catalogs: list[Catalog], view_config: ViewConfig):
        self.view_config = view_config
        self.ids_to_catalogs = {catalog.id: catalog for catalog in catalogs}

    def validate(self) -> None:
        logging.info(
            f"Validating view config {self.view_config.id!r} metrics against {len(self.ids_to_catalogs)} catalog(s)"
        )
        for full_metric_id in self.view_config.full_metric_ids:
            catalog_id, metric_id = full_metric_id.split(".")
            self._match_catalog_id(catalog_id)
            self._match_metric_id(catalog_id, metric_id)
        logging.info("All metrics are present in the catalogs")

    def _match_catalog_id(self, catalog_id: str) -> None:
        if catalog_id not in self.ids_to_catalogs:
            raise ValueError(f"Catalog {catalog_id!r} used in view config {self.view_config.id!r} doesn't exist!")

    def _match_metric_id(self, catalog_id: str, metric_id: str) -> None:
        if metric_id not in self.ids_to_catalogs[catalog_id].metrics:
            raise ValueError(
                f"Metric {metric_id!r} used in view config {self.view_config.id!r} doesn't exist in catalog {catalog_id!r}"
            )
