# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

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
