# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Explicit on-disk paths consumed by GEMS-ViewsBuilder (provided directly via CLI)."""

from argparse import Namespace
from pathlib import Path

from gems_views_builder.paths_resolver import PathsResolver


class InputPaths:
    def __init__(self, args: Namespace) -> None:
        self.libraries_dir: Path = Path(args.libraries_dir)
        self.catalogs: list[Path] = PathsResolver(args.catalogs).resolve()
        self.system: Path = Path(args.system)
        self.calendar: Path = Path(args.calendar)
        self.taxonomy: Path = Path(args.taxonomy)
        self.view_config: Path = Path(args.view_config)
        self.simulation_table: Path = Path(args.simulation_table)
