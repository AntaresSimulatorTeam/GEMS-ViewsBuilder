# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.validation.aggregation_patterns_validator import AggregationPatternsValidator
from gems_views_builder.validation.input_consistency_validator import InputConsistencyValidator
from gems_views_builder.validation.simulation_tables import validate_simulation_tables_consistency


def validate_input_data(raw_input_data: RawInputData) -> None:
    input_data_direct_validation(raw_input_data)
    InputConsistencyValidator(raw_input_data).validate()


def input_data_direct_validation(raw_input_data: RawInputData) -> None:
    validate_simulation_tables_consistency(raw_input_data.simulation_tables)
    AggregationPatternsValidator(raw_input_data.view_config.aggregation_patterns).validate()
