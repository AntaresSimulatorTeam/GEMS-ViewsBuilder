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

"""View (spec views.py)."""

from pathlib import Path

from gems.study.parsing import InputSystem, parse_yaml_components  # type: ignore[import-untyped]

from src.calendar import Calendar
from src.catalog import Catalog
from src.metrics import ViewConfig
from src.simulation_table import SimulationTable
from src.taxonomy import Taxonomy



