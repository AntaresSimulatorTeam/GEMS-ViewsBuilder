# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.validation.catalogs import validate_catalogs
from gems_views_builder.validation.input_consistency_validator import InputConsistencyValidator
from gems_views_builder.validation.simulation_tables import validate_simulation_tables_consistency
from gems_views_builder.validation.view_config import validate_view_configs


def validate_input_data(raw_input_data: RawInputData) -> None:
    input_data_direct_validation(raw_input_data)
    InputConsistencyValidator(raw_input_data).validate()


def input_data_direct_validation(raw_input_data: RawInputData) -> None:
    validate_simulation_tables_consistency(raw_input_data.simulation_tables)
    validate_view_configs(raw_input_data.view_configs)
    validate_catalogs(raw_input_data.catalogs)
