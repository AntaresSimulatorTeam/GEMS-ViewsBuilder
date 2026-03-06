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
from dataclasses import dataclass


@dataclass
class Taxonomy:
    """
    In memory representation of the taxonomy.yml file
    Key: category name
    Value: list of category values whose will be used as localization element.(In future, it will be a tree of categories.)
    """

    taxonomy_categories: dict[str, list[str]]
