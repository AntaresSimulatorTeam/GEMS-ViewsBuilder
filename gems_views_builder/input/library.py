# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Model library YAML with explicit local models"""

from dataclasses import dataclass
from typing import cast

from gems_craft.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema  # type: ignore


@dataclass
class Library:
    """
    library .yml representation with taxonomy indexes.
    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    id: str
    description: str
    port_types: list[PortTypeSchema]
    models: dict[str, ModelSchema]
    models_by_taxonomy_category: dict[str, list[str]]
    taxon_by_model: dict[str, str]

    def get_model(self, model_id: str) -> ModelSchema:
        try:
            return self.models[model_id]
        except KeyError:
            raise ValueError(f"Model {model_id} not found in library")

    def get_model_taxon(self, model_id: str) -> str:
        model = self.get_model(model_id)
        if model.taxonomy_category is None:
            raise ValueError(f"Model {model_id} has no taxonomy category in library")
        return cast(str, model.taxonomy_category)

    def get_models_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])


def create_lib_from_yml(yml_lib: LibrarySchema) -> Library:
    return Library(
        id=yml_lib.id,
        description=yml_lib.description or "",
        port_types=yml_lib.port_types,
        models={m.id: m for m in yml_lib.models},
        models_by_taxonomy_category={
            cat: [m.id for m in yml_lib.models if m.taxonomy_category == cat]
            for cat in {m.taxonomy_category for m in yml_lib.models if m.taxonomy_category}
        },
        taxon_by_model={m.id: m.taxonomy_category for m in yml_lib.models if m.taxonomy_category},
    )


def associate_models_with_a_taxon(libraries: dict[str, Library]) -> dict[str, str]:
    taxon_by_model: dict[str, str] = {}
    for library_id, library in libraries.items():
        for model_id, taxon in library.taxon_by_model.items():
            taxon_by_model[f"{library_id}.{model_id}"] = taxon
    return taxon_by_model
