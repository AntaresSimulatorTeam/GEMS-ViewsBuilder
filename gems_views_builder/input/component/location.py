# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    properties: dict[str, str]
