# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Shared Pydantic base model for all GEMS ViewsBuilder models."""

from pydantic import BaseModel, ConfigDict


class ViewBuilderBasedModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda snake: snake.replace("_", "-"),
        validate_by_name=True,
        validate_by_alias=True,
    )
