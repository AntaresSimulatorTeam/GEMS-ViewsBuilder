# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Explicit on-disk paths consumed by GEMS-ViewsBuilder (provided directly via CLI)."""

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path


class InputPaths:
    def __init__(self, args: Namespace) -> None:
        self.libraries_dir: Path = Path(args.libraries_dir)
        self.catalogs_dir: Path = Path(args.catalogs_dir)
        self.system: Path = Path(args.system)
        self.calendar: Path = Path(args.calendar)
        self.taxonomy: Path = Path(args.taxonomy)
        self.view_config: Path = Path(args.view_config)
        self.simulation_tables: list[Path] = SimulationTablesPathsResolver(args.simulation_tables).resolve()


@dataclass
class SimulationTablesPathsResolver:
    """
    Recommended pattern: fake_path/output-xxx/st-x-mc-*.parquet
    """

    simulation_tables_pattern: str

    def resolve(self) -> list[Path]:
        glob_path = Path(self.simulation_tables_pattern)
        directory = glob_path.parent
        if not directory.is_dir():
            raise NotADirectoryError(f"Simulation tables directory does not exist: {directory}")

        return list(path for path in directory.glob(glob_path.name) if path.is_file())
