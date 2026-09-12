# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.view_config import ViewConfig


class ViewConfigMetricsAgainstCatalogsValidator:
    def __init__(self, catalogs: list[Catalog], view_config: ViewConfig):
        self.view_config = view_config
        self.view_config_id = view_config.id
        self.catalogs = {catalog.id: catalog for catalog in catalogs}

    def validate(self) -> None:
        logging.info(f"Validating view config {self.view_config_id!r} metrics against {len(self.catalogs)} catalog(s)")
        self.validate_used_metric_ids()
        logging.info("All metrics are present in the catalogs")

    def validate_used_metric_ids(self) -> None:
        for metric_ref in self.view_config.metric_ids:
            validate_metric_ref(metric_ref)
            catalog_id, metric_id = metric_ref.split(".", 1)
            self._match_catalog_id(catalog_id)
            self._match_metric_id(catalog_id, metric_id)

    def _match_catalog_id(self, catalog_id: str) -> None:
        if catalog_id not in self.catalogs:
            raise ValueError(f"Catalog {catalog_id} used in view config {self.view_config_id!r} doesn't exist!")

    def _match_metric_id(self, catalog_id: str, metric_id: str) -> None:
        if metric_id not in self.catalogs[catalog_id].metrics:
            raise ValueError(
                f"Metric {metric_id} used in view config {self.view_config_id!r} doesn't exist in catalog {catalog_id!r}"
            )


def validate_metric_ref(metric_ref: str) -> None:
    if metric_ref.count(".") != 1:
        raise ValueError(f"Invalid metric id '{metric_ref}'. Expected format '<catalog_id>.<metric_id>'")

    if metric_ref.startswith(".") or metric_ref.endswith("."):
        raise ValueError(f"Invalid metric id '{metric_ref}'. Expected format '<catalog_id>.<metric_id>'")
