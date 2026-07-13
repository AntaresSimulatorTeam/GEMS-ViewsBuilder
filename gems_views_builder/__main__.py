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
from gems_views_builder.common import (
    configure_logging,
    create_components,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.component import group_components_by_taxonomy_category
from gems_views_builder.loader import Loader
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.catalog_view_config_validator import validate_catalogs_against_view_config
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def run(input_dir: Path, view_sinker: ViewSinker) -> None:
    """Run the full pipeline and accumulate the results to the results directory."""

    # # Validate study layout
    StudyLayoutValidator(input_dir).validate()

    # # If everything is ok, load pipeline input
    input_data, catalogs = Loader(input_dir).load()

    # # This could be grouped,now main is messy
    ViewConfigTaxonomyValidator(input_data.taxonomy, input_data.view_config).validate()
    # # Validate catalogs against taxonomy and view config

    validate_catalogs_against_taxonomy(catalogs, input_data.taxonomy)
    validate_catalogs_against_view_config(catalogs, input_data.view_config)

    # # Create GVB components from system raw components
    components = create_components(input_data.system.components)
    supply_components_with_taxonomy_categories(components, input_data.library.taxonomy_category_by_model)
    supply_components_with_port_connections(components, input_data.system.connections)
    components_by_taxonomy_category = group_components_by_taxonomy_category(components)

    # # Only one instance of MetricStructureTableBuilder is needed
    metric_structure_table_builder = MetricStructureTableBuilder(
        input_data.view_config.location_taxonomy_category,
        components_by_taxonomy_category,
    )

    metric_views = ViewBuilder(input_data, metric_structure_table_builder).build()
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
