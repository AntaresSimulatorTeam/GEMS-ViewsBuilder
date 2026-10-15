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
        seen_metric_ids: set[str] = set()
        for full_metric_id in self.view_config.full_metric_ids:
            check_is_well_formed(full_metric_id)
            catalog_id, metric_id = full_metric_id.split(".", 1)
            self._match_catalog_id(catalog_id)
            self._match_metric_id(catalog_id, metric_id)
            self._match_unique_metric_id(metric_id, seen_metric_ids)
        logging.info("All metrics are present in the catalogs")

    def _match_catalog_id(self, catalog_id: str) -> None:
        if catalog_id not in self.ids_to_catalogs:
            raise ValueError(f"Catalog {catalog_id} used in view config {self.view_config.id!r} doesn't exist!")

    def _match_metric_id(self, catalog_id: str, metric_id: str) -> None:
        if metric_id not in self.ids_to_catalogs[catalog_id].metrics:
            raise ValueError(
                f"Metric {metric_id} used in view config {self.view_config.id!r} doesn't exist in catalog {catalog_id!r}"
            )

    def _match_unique_metric_id(self, metric_id: str, seen_metric_ids: set[str]) -> None:
        if metric_id in seen_metric_ids:
            raise ValueError(
                f"metric ids are not unique: {metric_id!r} is selected more than once "
                f"in view config {self.view_config.id!r}"
            )
        seen_metric_ids.add(metric_id)


def check_is_well_formed(full_metric_id: str) -> None:
    if full_metric_id.count(".") != 1 or full_metric_id.startswith(".") or full_metric_id.endswith("."):
        raise ValueError(f"Invalid metric id '{full_metric_id}'. Expected format '<catalog_id>.<metric_id>'")
