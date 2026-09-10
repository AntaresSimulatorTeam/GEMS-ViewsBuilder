# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from collections import defaultdict
from copy import deepcopy

from gems_views_builder.aggregators.aggregations_processor import AgggregationProcessor
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
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.input_paths_validator import InputPathsValidator
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def load_and_validate_input_data(input_paths: InputPaths) -> RawInputData:
    raw_input_data = Loader(input_paths).load()
    validate_catalogs_against_taxonomy(raw_input_data.catalogs, raw_input_data.taxonomy)
    return raw_input_data


def build_metric_views(
    view_building_inputs: list[ViewBuildingInputData],
    components_by_taxon: dict[str, list[Component]],
) -> dict[str, list[TemporalMetricView]]:
    metric_views_by_view_config: dict[str, list[TemporalMetricView]] = defaultdict(list)
    for view_building_input in view_building_inputs:
        metric_views = build_metric_views_for_view_config(view_building_input, components_by_taxon)
        metric_views_by_view_config[view_building_input.view_config.id].extend(metric_views)
    return metric_views_by_view_config


def build_metric_views_for_view_config(
    view_building_input: ViewBuildingInputData, components_by_taxon: dict[str, list[Component]]
) -> list[TemporalMetricView]:
    components_by_taxon = deepcopy(components_by_taxon)
    supply_components_with_locations(
        components_by_taxon,
        view_building_input.view_config.get_metrics(),
        view_building_input.view_config.location_taxonomy_category,
    )

    metric_structure_table_builder = MetricStructureTableBuilder(
        view_building_input.view_config,
        components_by_taxon,
    )
    aggregation_processor = AgggregationProcessor(view_building_input.view_config)
    return ViewBuilder(view_building_input, metric_structure_table_builder, aggregation_processor).build()


def run_view_building_process(input_paths: InputPaths, view_sinker: ViewSinker) -> None:
    raw_input_data = load_and_validate_input_data(input_paths)
    view_building_inputs = create_view_building_inputs(raw_input_data)

    # Components : create, enrich and group by taxon
    components = create_components(raw_input_data.system.components)
    enrich_components(components, raw_input_data)
    components_by_taxon = group_components_by_taxon(components)

    metric_views_by_view_config = build_metric_views(view_building_inputs, components_by_taxon)

    accumulate_on_disk(metric_views_by_view_config, view_sinker)


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
