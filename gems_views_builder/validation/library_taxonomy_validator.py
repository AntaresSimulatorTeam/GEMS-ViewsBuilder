# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from gems_craft.model.parsing import LibrarySchema  # type: ignore
from gems_craft.model.taxonomy import Taxonomy, check_library_against_taxonomy  # type: ignore

from gems_views_builder.input.library import Library


def validate_libraries_against_taxonomy(libraries: dict[str, Library], taxonomy: Taxonomy) -> None:
    for library in libraries.values():
        check_library_against_taxonomy(to_library_schema(library), taxonomy)


def to_library_schema(library: Library) -> LibrarySchema:
    return LibrarySchema(id=library.id, port_types=library.port_types, models=list(library.models.values()))
