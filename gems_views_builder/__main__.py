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
)
from gems_views_builder.input.component import (
    build_component_port_connections,
    create_components,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.loader import Loader
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.validation.input_consistency_validator import InputConsistencyValidator
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def run_view_building_process(input_dir: Path, view_sinker: ViewSinker) -> None:
    """Run the full pipeline and accumulate the results to the results directory."""

    # # Validate study layout
    StudyLayoutValidator(input_dir).validate()

    # # If everything is ok, load pipeline input
    input_data, catalogs = Loader(input_dir).load()

    InputConsistencyValidator(catalogs, input_data).validate()

    # # Create GVB components from system raw components
    components = create_components(input_data.system.components)
    supply_components_with_taxonomy_categories(components, input_data.library.taxonomy_category_by_model)
    component_port_connections = build_component_port_connections(input_data.system.connections)
    supply_components_with_port_connections(components, component_port_connections)
    components_by_taxon = group_components_by_taxon(components)
    supply_components_with_locations(
        components_by_taxon,
        input_data.view_config.get_metrics(),
        input_data.view_config.location_taxonomy_category,
    )

    # # Only one instance of MetricStructureTableBuilder is needed
    metric_structure_table_builder = MetricStructureTableBuilder(
        input_data.view_config.location_taxonomy_category,
        components_by_taxon,
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
        StudyLayoutValidator(args.input_dir).validate()
        run_view_building_process(args.input_dir, view_sinker)
    except Exception:
        logging.exception("View building failed")
        return 1

    logging.info(f"View successfully written to {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
