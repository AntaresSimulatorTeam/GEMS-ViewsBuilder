<<<<<<< HEAD
# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

=======
>>>>>>> origin/main
"""Cross-artifact and study-layout validation."""

from gems_views_builder.validation.catalog_taxonomy_validator import (
    validate_catalog_against_taxonomy,
    validate_catalogs_against_taxonomy,
)
from gems_views_builder.validation.study_layout_validator import (
    EXACT_FILES,
    PREFIX_FILES,
    StudyLayoutValidator,
)

__all__ = [
    "EXACT_FILES",
    "PREFIX_FILES",
    "StudyLayoutValidator",
    "validate_catalog_against_taxonomy",
    "validate_catalogs_against_taxonomy",
]
