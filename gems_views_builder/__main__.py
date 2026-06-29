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

import logging
from pathlib import Path

from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.common import accumulate_on_disk, configure_logging, make_log_file
from gems_views_builder.loader import Loader
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.views_builder import ViewBuilder


def run(input_dir: Path, results_dir: Path) -> None:
    """Run the full pipeline and save the results to the results directory."""

    # # Validate study layout
    StudyLayoutValidator(input_dir).validate()
    # # If everything is ok, load pipeline input
    input_data = Loader(input_dir).load()
    # # Validate catalogs against taxonomy
    validate_catalogs_against_taxonomy(input_data.catalogs, input_data.taxonomy)

    metric_views = ViewBuilder(input_data).build()
    accumulate_on_disk(metric_views, results_dir)


def main(argv: list[str] | None = None) -> int:
    """
    0 - Success
    1 - Pipeline ran but throw exception
    2 - Bad/Invalid command line usage/inputs
    """
    args = build_parser().parse_args(argv)
    log_file = make_log_file(log_dir=args.log_dir)
    configure_logging(verbose=args.verbose, log_file=log_file)
    logging.info(f"Logging to {log_file}")

    error = check_options(args)
    if error is not None:
        return error

    try:
        run(args.input_dir, args.results_dir)
    except Exception:
        logging.exception("View building failed")
        return 1

    logging.info(f"View successfully written to {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
