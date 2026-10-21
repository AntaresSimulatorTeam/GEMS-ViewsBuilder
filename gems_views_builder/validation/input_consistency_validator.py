# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Orchestrate cross-artifact validation between the loaded catalogs, taxonomy and view config."""

from collections import defaultdict
from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.raw_input_data import RawInputData
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
        catalogs_by_view_configs = group_catalogs_by_view_configs(self.raw_input_data, catalogs_by_ids)
        for view_config in self.raw_input_data.view_configs:
            ViewConfigTaxonomyValidator(self.raw_input_data.taxonomy, view_config).validate()
            ViewConfigCatalogsValidator(catalogs_by_view_configs[view_config.id], view_config).validate()
            ViewConfigMetricsAgainstCatalogsValidator(catalogs_by_view_configs[view_config.id], view_config).validate()


def group_catalogs_by_view_configs(
    raw_input_data: RawInputData, catalogs_by_ids: dict[str, Catalog]
) -> defaultdict[str, list[Catalog]]:
    catalogs_by_view_configs: defaultdict[str, list[Catalog]] = defaultdict(list)
    for view_config in raw_input_data.view_configs:
        catalog_ids: set[str] = set()
        for full_metric_id in view_config.full_metric_ids:
            catalog_id, _ = full_metric_id.split(".", 1)
            if catalog_id in catalog_ids:
                continue
            catalog_ids.add(catalog_id)
            catalogs_by_view_configs[view_config.id].append(catalogs_by_ids[catalog_id])
    return catalogs_by_view_configs
