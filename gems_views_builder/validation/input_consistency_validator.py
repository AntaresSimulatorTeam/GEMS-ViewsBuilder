# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Orchestrate cross-artifact validation between the loaded catalogs, taxonomy and view config."""

from dataclasses import dataclass

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator
from gems_views_builder.validation.catalogs_view_config_validator import CatalogsViewConfigValidator
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator


@dataclass
class InputConsistencyValidator:
    raw_input_data: RawInputData

    def validate(self) -> None:
        ViewConfigTaxonomyValidator(self.raw_input_data.taxonomy, self.raw_input_data.view_config).validate()
        CatalogsTaxonomyValidator(self.raw_input_data.catalogs, self.raw_input_data.taxonomy).validate()
        CatalogsViewConfigValidator(self.raw_input_data.catalogs, self.raw_input_data.view_config).validate()
