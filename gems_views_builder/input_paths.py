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
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InputPaths:
    libraries_dir: Path
    catalogs_dir: Path
    system: Path
    calendar: Path
    taxonomy: Path
    view_config: Path
    simulation_table: Path

    @property
    def library_file(self) -> Path:
        """Single library file currently supported under libraries_dir."""
        return self.libraries_dir / "library.yml"


def create_input_paths_from_args(args: Namespace) -> InputPaths:
    return InputPaths(
        libraries_dir=args.libraries_dir,
        catalogs_dir=args.catalogs_dir,
        system=args.system,
        calendar=args.calendar,
        taxonomy=args.taxonomy,
        view_config=args.view_config,
        simulation_table=args.simulation_table,
    )
