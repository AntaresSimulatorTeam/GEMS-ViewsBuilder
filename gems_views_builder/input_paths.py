# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Explicit on-disk paths consumed by GEMS-ViewsBuilder (provided directly via CLI)."""

from argparse import Namespace
from pathlib import Path

from gems_views_builder.multiple_files_collector import collect_files, collect_yml_from_dir


class InputPaths:
    def __init__(self, args: Namespace) -> None:
        self.libraries: list[Path] = collect_yml_from_dir(args.libraries_dir)
        self.catalogs: list[Path] = collect_yml_from_dir(args.catalogs_dir)
        self.system: Path = Path(args.system)
        self.calendar: Path = Path(args.calendar)
        self.taxonomy: Path = Path(args.taxonomy)
        self.view_configs: list[Path] = collect_files(args.view_configs)
        self.simulation_tables: list[Path] = collect_files(args.simulation_tables)
