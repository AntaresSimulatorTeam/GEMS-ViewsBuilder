# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from gems_craft.model.parsing import LibrarySchema  # type: ignore
from gems_craft.model.taxonomy import Taxonomy, check_library_against_taxonomy  # type: ignore


def validate_libraries_against_taxonomy(library_schemas: list[LibrarySchema], taxonomy: Taxonomy) -> None:
    for library_schema in library_schemas:
        check_library_against_taxonomy(library_schema, taxonomy)
