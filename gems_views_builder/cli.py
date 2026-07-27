# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

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
        help=(
            "GEMS View Builder input directory (contains input/model-libraries, input/catalogs, input/taxonomy, "
            "input/view-configs, input/system.yml, and output/{simulation_id}/simulation_table.*). "
            "Results are written to output/{simulation_id}/views/ of the most recent simulation."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="results_dir",
        type=Path,
        default=None,
        help=(
            "Directory where the result file will be written. If omitted, defaults to "
            "output/{simulation_id}/views/ (most recent simulation) under the input directory."
        ),
    )
    parser.add_argument(
        "-f",
        "--output-format",
        dest="output_format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Format of the merged result file (default: parquet).",
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
    if args.results_dir is not None and not args.results_dir.is_dir():
        logging.error(f"Results directory does not exist: {args.results_dir}")
        return 2
    return None
