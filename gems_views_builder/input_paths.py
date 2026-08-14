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

"""Explicit on-disk paths consumed by GEMS-ViewsBuilder (provided directly via CLI)."""

from argparse import Namespace
from pathlib import Path


class InputPaths:
    def __init__(self, args: Namespace) -> None:
        self.libraries_dir: Path = Path(args.libraries_dir)
        self.catalogs_dir: Path = Path(args.catalogs_dir)
        self.system: Path = Path(args.system)
        self.calendar: Path = Path(args.calendar)
        self.taxonomy: Path = Path(args.taxonomy)
        self.view_config: Path = Path(args.view_config)
        self.simulation_table: Path = Path(args.simulation_table)

    @property
    def library_file(self) -> Path:
        """Single library file currently supported under libraries_dir."""
        return self.libraries_dir / "library.yml"
