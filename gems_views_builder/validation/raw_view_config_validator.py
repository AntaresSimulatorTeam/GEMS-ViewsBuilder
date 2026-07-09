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

"""Validate business rules on a parsed RawViewConfig that Pydantic cannot express."""

from dataclasses import dataclass

from gems_views_builder.input.view_config import RawViewConfig


@dataclass
class RawViewConfigValidator:
    raw_view_config: RawViewConfig

    def validate(self) -> None:
        self._validate_location()
        self._validate_calendar()

    def _validate_location(self) -> None:
        locations = [item.location for item in self.raw_view_config.scope if item.location is not None]
        if len(locations) != 1:
            raise ValueError(
                f"view_config.yml '{self.raw_view_config.id}': expected exactly one location in scope, "
                f"found {len(locations)}"
            )
        if locations[0].taxonomy_category is None:
            raise ValueError(f"view_config.yml '{self.raw_view_config.id}': location taxonomy category is required")

    def _validate_calendar(self) -> None:
        calendars = [item.calendar for item in self.raw_view_config.scope if item.calendar is not None]
        if len(calendars) != 1:
            raise ValueError(
                f"view_config.yml '{self.raw_view_config.id}': expected exactly one calendar in scope, "
                f"found {len(calendars)}"
            )
        if calendars[0].id is None:
            raise ValueError(f"view_config.yml '{self.raw_view_config.id}': calendar id is required")
