# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging

from gems_views_builder.aggregators.aggregations_processor import AggregationProcessor
from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.common import (
    configure_logging,
)
from gems_views_builder.input.component import (
    Component,
    create_components,
    enrich_components,
    group_components_by_taxon,
    supply_components_with_locations,
)
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData, create_view_building_inputs
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.validation.input_consistency_validator import InputConsistencyValidator
from gems_views_builder.validation.input_paths_validator import InputPathsValidator
from gems_views_builder.validation.view_config import validate_view_configs
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def load_and_validate_input_data(input_paths: InputPaths) -> RawInputData:
    raw_input_data = Loader(input_paths).load()
    validate_view_configs(raw_input_data.view_configs)
    InputConsistencyValidator(raw_input_data).validate()
    return raw_input_data


def create_view_builder(
    view_building_input: ViewBuildingInputData,
    components_by_taxon: dict[str, list[Component]],
) -> ViewBuilder:
    supply_components_with_locations(
        components_by_taxon,
        view_building_input.view_config.get_metrics(),
        view_building_input.view_config.location_taxonomy_category,
    )
    metric_structure_table_builder = MetricStructureTableBuilder(
        view_building_input.view_config,
        components_by_taxon,
    )
    aggregation_processor = AggregationProcessor(view_building_input.view_config)
    return ViewBuilder(view_building_input, metric_structure_table_builder, aggregation_processor)


def build_components_by_taxon(raw_input_data: RawInputData) -> dict[str, list[Component]]:
    components = create_components(raw_input_data.system.components)
    enrich_components(components, raw_input_data)
    return group_components_by_taxon(components)


def build_metric_views(
    view_building_input: ViewBuildingInputData,
    components_by_taxon: dict[str, list[Component]],
) -> list[TemporalMetricView]:
    return create_view_builder(view_building_input, components_by_taxon).build()


def run_view_building_process(input_paths: InputPaths, view_sinker: ViewSinker) -> None:
    raw_input_data = load_and_validate_input_data(input_paths)
    components_by_taxon = build_components_by_taxon(raw_input_data)
    for view_building_input in create_view_building_inputs(raw_input_data):
        metric_views = build_metric_views(view_building_input, components_by_taxon)
        accumulate_on_disk(metric_views, view_sinker)
        # Drop this config's intermediate parquet files before the next config is built.
        del metric_views


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose, log_dir=args.log_dir)

    try:
        check_options(args)
    except Exception as e:
        raise ValueError(f"Command lines options : {str(e)}") from e

    try:
        logging.info("Starting view building process")
        input_paths = InputPaths(args)
        InputPathsValidator(input_paths).validate()
        view_sinker = ViewSinkerFactory(args.output, args.output_format).make()
        run_view_building_process(input_paths, view_sinker)
    except Exception as e:
        # from e will keep upper level exception message
        raise ValueError(f"View building failed: {e}") from e

    logging.info(f"View successfully written to {view_sinker.output_path}")


if __name__ == "__main__":
    main()
