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

"""Command line interface for GEMS-ViewsBuilder."""

import argparse
import logging
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gems-views-builder",
        description="Build aggregated metric views from a GEMS simulation dataset.",
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Input data directory (contains view_config.yml, simulation_table*.parquet, library.yml, ...).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="results_dir",
        type=Path,
        required=True,
        help="Directory where the merged result parquet will be written.",
    )
    parser.add_argument(
        "-l",
        "--log-dir",
        type=Path,
        help="Directory where the logs will be written.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose console logging.",
    )
    return parser


def check_options(args: argparse.Namespace) -> int | None:
    if not args.input_dir.is_dir():
        logging.error(f"Input directory does not exist: {args.input_dir}")
        return 2
    if not args.results_dir.is_dir():
        logging.error(f"Results directory does not exist: {args.results_dir}")
        return 2
    return None
