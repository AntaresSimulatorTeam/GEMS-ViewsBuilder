from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.input_data import InputData
from gems_views_builder.validation.catalog_view_config_validator import CatalogsViewConfigValidator
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator


@dataclass
class InputConsistencyValidator:
    catalogs: list[Catalog]
    input_data: InputData

    def validate(self) -> None:
        ViewConfigTaxonomyValidator(self.input_data.taxonomy, self.input_data.view_config).validate()
        CatalogsTaxonomyValidator(self.catalogs, self.input_data.taxonomy).validate()
        # # Note: In close future when we will have multiple view configs, we will need to validate against all of them
        CatalogsViewConfigValidator(self.catalogs, self.input_data.view_config).validate()
