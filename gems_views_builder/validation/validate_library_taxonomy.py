# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from gems_craft.model.taxonomy import Taxonomy  # type: ignore

try:
    from gems_craft.model.validation import check_library_against_taxonomy  # type: ignore
except ImportError:  # gemspy <= 0.2.0
    from gems_craft.model.taxonomy import check_library_against_taxonomy

from gems_views_builder.input.library import Library


def validate_libraries_against_taxonomy(libraries: list[Library], taxonomy: Taxonomy) -> None:
    for library in libraries:
        check_library_against_taxonomy(library, taxonomy)
