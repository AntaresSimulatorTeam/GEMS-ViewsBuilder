# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging

from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.common import (
    configure_logging,
)
from gems_views_builder.input.component import (
    create_components,
    enrich_components,
    group_components_by_taxon,
    supply_components_with_locations,
)
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_building_input_data import create_view_building_input
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.input_paths_validator import InputPathsValidator
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def load_and_validate_input_data(input_paths: InputPaths) -> RawInputData:
    raw_input_data = Loader(input_paths).load()
    validate_catalogs_against_taxonomy(
        input_paths.catalogs_dir, raw_input_data.view_config.catalog_ids, raw_input_data.taxonomy
    )
    return raw_input_data


def build_metric_views(raw_input_data: RawInputData) -> list[MetricView]:
    components = create_components(raw_input_data.system.components)
    enrich_components(components, raw_input_data)
    components_by_taxon = group_components_by_taxon(components)

    view_building_input = create_view_building_input(raw_input_data)
    supply_components_with_locations(
        components_by_taxon,
        view_building_input.view_config.get_metrics(),
        view_building_input.view_config.location_taxonomy_category,
    )

    metric_structure_table_builder = MetricStructureTableBuilder(
        view_building_input.view_config,
        components_by_taxon,
    )
    return ViewBuilder(view_building_input, metric_structure_table_builder).build()


def run_view_building_process(input_paths: InputPaths, view_sinker: ViewSinker) -> None:
    raw_input_data = load_and_validate_input_data(input_paths)
    metric_views = build_metric_views(raw_input_data)
    accumulate_on_disk(metric_views, view_sinker)


def main(argv: list[str] | None = None) -> int:
    """
    0 - Success
    1 - Pipeline ran but throw exception
    2 - Bad/Invalid command line usage/inputs
    """
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose, log_dir=args.log_dir)

    try:
        check_options(args)
    except Exception:
        return 2

    try:
        input_paths = InputPaths(args)
        InputPathsValidator(input_paths).validate()
        view_sinker = ViewSinkerFactory(args.output, args.output_format).make()
        run_view_building_process(input_paths, view_sinker)
    except Exception:
        logging.exception("View building failed")
        return 1

    logging.info(f"View successfully written to {view_sinker.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
