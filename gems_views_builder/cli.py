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

from gems_views_builder.common import configure_logging
from gems_views_builder.loader import Loader
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.views_builder import ViewBuilder


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


def run(input_dir: Path, results_dir: Path) -> Path:
    """Run the full pipeline and return the path to the merged view parquet."""

    # # Validate study layout
    StudyLayoutValidator(input_dir).validate()
    # # If everything is ok, load pipeline input
    input_data = Loader(input_dir, results_dir).load()
    # # Validate catalogs against taxonomy
    validate_catalogs_against_taxonomy(input_data.catalogs, input_data.taxonomy)

    merged_view = ViewBuilder(input_data).build()
    return merged_view.result_path


def main(argv: list[str] | None = None) -> int:
    """
    0 - Success
    1 - Pipeline ran but throw exception
    2 - Bad/Invalid command line usage/inputs
    """
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)

    if not args.input_dir.is_dir():
        logging.error(f"Input directory does not exist: {args.input_dir}")
        return 2

    if not args.results_dir.is_dir():
        logging.error(f"Results directory does not exist: {args.results_dir}")
        return 2

    try:
        result_path = run(args.input_dir, args.results_dir)
    except Exception:
        logging.exception("View building failed")
        return 1

    logging.info(f"View successfully written to {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
