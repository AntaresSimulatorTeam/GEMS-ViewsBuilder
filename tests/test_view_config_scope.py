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

from pathlib import Path

import pytest
from pydantic import ValidationError

from gems_views_builder.input.view_config import load_raw_view_config_file, load_view_config


def _write_view_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(body.strip())
    return config_path


def test_scope_loads_location_and_calendar(test_dataset_dir: Path) -> None:
    scope = load_raw_view_config_file(test_dataset_dir / "view_config.yml").scope
    assert scope.location.taxonomy_category == "balance"
    assert scope.calendar.id == "calendar_file"


@pytest.mark.parametrize(
    "scope_body",
    [
        "  scope:\n    calendar:\n      id: calendar_file",
        "  scope:\n    location:\n      taxonomy-category: balance",
    ],
)
def test_scope_requires_location_and_calendar(tmp_path: Path, scope_body: str) -> None:
    config_path = _write_view_config(
        tmp_path,
        f"""
view:
  id: incomplete_scope
{scope_body}
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    id: my_taxonomy
  metrics:
    - id: catalog.LOAD
""",
    )
    with pytest.raises(ValidationError):
        load_view_config(config_path)
