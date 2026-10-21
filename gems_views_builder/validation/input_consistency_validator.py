# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Orchestrate cross-artifact validation between the loaded catalogs, taxonomy and view config."""

from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator
from gems_views_builder.validation.catalogs_view_config_validator import ViewConfigCatalogsValidator
from gems_views_builder.validation.view_config_metrics_against_catalogs_validator import (
    ViewConfigMetricsAgainstCatalogsValidator,
)
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator


@dataclass
class InputConsistencyValidator:
    raw_input_data: RawInputData

    def validate(self) -> None:
        CatalogsTaxonomyValidator(self.raw_input_data.catalogs, self.raw_input_data.taxonomy).validate()
        catalogs_by_ids = {catalog.id: catalog for catalog in self.raw_input_data.catalogs}
        for view_config in self.raw_input_data.view_configs:
            view_config_catalogs = associated_catalogs(view_config, catalogs_by_ids)

            ViewConfigTaxonomyValidator(self.raw_input_data.taxonomy, view_config).validate()
            ViewConfigCatalogsValidator(view_config_catalogs, view_config).validate()
            ViewConfigMetricsAgainstCatalogsValidator(view_config_catalogs, view_config).validate()

def associated_catalogs(view_config: ViewConfig, catalogs_by_ids: dict[str, Catalog]) -> list[Catalog]:
    catalogs: list[Catalog] = []
    catalogs_already_added: set[str] = set()
    for full_metric_id in view_config.full_metric_ids:
        catalog_id, _ = full_metric_id.split(".", 1)
        if catalog_id not in catalogs_by_ids:
            raise ValueError(f"Catalog {catalog_id!r} referenced by view config {view_config.id!r} does not exist")
        if catalog_id not in catalogs_already_added:
            catalogs.append(catalogs_by_ids[catalog_id])
            catalogs_already_added.add(catalog_id)
    return catalogs