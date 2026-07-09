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
from gems_views_builder.common import configure_logging
from gems_views_builder.loader import Loader
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def run(input_dir: Path, view_sinker: ViewSinker) -> None:
    """Run the full pipeline and accumulate the results to the results directory."""

    # # Validate study layout
    StudyLayoutValidator(input_dir).validate()
    # # If everything is ok, load pipeline input
    input_data = Loader(input_dir).load()

    ViewConfigTaxonomyValidator(input_data.taxonomy, input_data.view_config).validate()

    # # Validate catalogs against taxonomy
    validate_catalogs_against_taxonomy(input_dir, input_data.view_config.catalog_ids, input_data.taxonomy)

    metric_views = ViewBuilder(input_data).build()
    accumulate_on_disk(metric_views, view_sinker)


def main(argv: list[str] | None = None) -> int:
    """
    0 - Success
    1 - Pipeline ran but throw exception
    2 - Bad/Invalid command line usage/inputs
    """
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose, log_dir=args.log_dir)
    view_sinker = ViewSinkerFactory(args.results_dir, args.output_format).make()

    error = check_options(args)
    if error is not None:
        return error

    try:
        run(args.input_dir, view_sinker)
    except Exception:
        logging.exception("View building failed")
        return 1

    logging.info(f"View successfully written to {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
