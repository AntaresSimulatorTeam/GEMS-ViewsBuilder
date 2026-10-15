# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Build the area and link views of this example into output/area and output/link (Linux, macOS and Windows)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).parent

for view in ("area", "link"):
    (EXAMPLE_DIR / "output" / view).mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "gems_views_builder",
            "--system",
            "inputs/system-for-views.yml",
            "--libraries-dir",
            "inputs/libraries",
            "--taxonomy",
            "inputs/antares_legacy_taxonomy_flattened.yml",
            "--catalogs-dir",
            "inputs/catalogs",
            "--calendar",
            "inputs/calendar.csv",
            "--simulation-tables",
            "inputs/simulation_tables/simulation-table-*-optim-nb-2.parquet",
            "--view-config",
            f"inputs/view_config_{view}.yml",
            "--output",
            f"output/{view}",
            "--output-format",
            "csv",
        ],
        cwd=EXAMPLE_DIR,
        check=True,
    )
