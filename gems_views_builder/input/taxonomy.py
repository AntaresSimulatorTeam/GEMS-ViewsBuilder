# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass, field

from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel


class TaxonomyItem(ViewBuilderBasedModel):
    id: str


class TaxonomyCategory(ViewBuilderBasedModel):
    id: str
    parent_category: str | None = Field(
        None, alias="parent-category"
    )  # for now keep like this because taxonomy.yml used for testing isn't completed
    variables: list[TaxonomyItem] = Field(default_factory=list)
    parameters: list[TaxonomyItem] = Field(default_factory=list)
    ports: list[TaxonomyItem] = Field(default_factory=list)
    constraints: list[TaxonomyItem] = Field(default_factory=list)
    extra_outputs: list[TaxonomyItem] = Field(default_factory=list)
    properties: list[TaxonomyItem] = Field(default_factory=list)

    @property
    def port_ids(self) -> set[str]:
        return {port.id for port in self.ports}


class TaxonomyData(ViewBuilderBasedModel):
    id: str
    description: str = ""
    categories: list[TaxonomyCategory] = Field(default_factory=list)


@dataclass
class Taxonomy:
    """
    Parsed taxonomy.yml representation used by the view builder.
    """

    id: str
    description: str = ""
    categories: dict[str, TaxonomyCategory] = field(default_factory=dict)


def allowed_output(taxon: TaxonomyCategory) -> set[str]:
    return {var.id for var in taxon.variables} | {extra_output.id for extra_output in taxon.extra_outputs}
