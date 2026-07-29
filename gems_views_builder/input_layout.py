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

"""Resolves the on-disk layout GEMS-ViewsBuilder (GVB) expects: input/ subfolders and the
latest output/ simulation folder, rooted at the GVB input directory (input_dir).

input_dir holds the GEMS study data plus GVB-specific

    input_dir/
    |-- input/
    |   |-- model-libraries/   (library.yml) - in future multiple files
    |   |-- catalogs/          (*.yml, one or more)
    |   |-- taxonomy/          (taxonomy.yml) - fixed one file
    |   |-- view-configs/      (view_config.yml) - in future multiple files
    |   |-- system.yml
    |   `-- calendar*.csv
    `-- output/
        `-- {simulation_id}/   (most recent by folder name)
            |-- simulation_table.{parquet,csv}
            `-- views/         (created by GVB, unless -o/--output overrides it)
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class InputLayout:
    root_dir: Path

    @property
    def input_dir(self) -> Path:
        return self.root_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.root_dir / "output"

    @property
    def model_libraries_path(self) -> Path:
        return self.input_dir / "model-libraries" / "library.yml"

    @property
    def catalogs_dir(self) -> Path:
        return self.input_dir / "catalogs"

    @property
    def taxonomy_path(self) -> Path:
        return self.input_dir / "taxonomy" / "taxonomy.yml"

    @property
    def view_config_path(self) -> Path:
        return self.input_dir / "view-configs" / "view_config.yml"

    @property
    def system_file(self) -> Path:
        return self.input_dir / "system.yml"

    @property
    def calendar_path(self) -> Path:
        return self.input_dir / "calendar.csv"

    @property
    def simulation_dir(self) -> Path:
        return resolve_latest_simulation_dir(self.output_dir)

    @property
    def simulation_table_path(self) -> Path:
        return next(p for p in self.simulation_dir.iterdir() if p.is_file() and p.name.startswith("simulation_table"))

    def views_output_dir(self, simulation_dir: Path) -> Path:
        return simulation_dir / "views"


def resolve_latest_simulation_dir(output_dir: Path) -> Path:
    """
    Sort simulation dirs by name, return the most recent one.
    Directory name, e.g. "20260727-1200".
    For consideration: do we want to use latest one or give user ability to choose?
    (Since we're currently supporting only one view config file)
    """
    if not output_dir.is_dir():
        raise NotADirectoryError(f"Output directory {output_dir} not found or not a directory")
    simulation_dirs = sorted((d for d in output_dir.iterdir() if d.is_dir()), key=lambda d: d.name)
    if not simulation_dirs:
        raise FileNotFoundError(f"No simulation folder found in {output_dir}")
    return simulation_dirs[-1]
