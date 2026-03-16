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

from src.metrics import TimeAggregation, ViewConfig

TEST_FILES_ROOT = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files"

CONFIG_PATHS = [
    TEST_FILES_ROOT / "input_one_daily" / "view_config.yml",
    TEST_FILES_ROOT / "input_two_hourly" / "view_config.yml",
]


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_loads(config_path: Path) -> None:
    config = ViewConfig(config_path)
    assert isinstance(config.id, str)
    assert isinstance(config.location_taxonomy_category, str)
    assert isinstance(config.calendar_id, str)
    assert len(config.catalog_ids) > 0
    assert len(config.metrics) > 0


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_catalog_ids_are_strings(config_path: Path) -> None:
    config = ViewConfig(config_path)
    for catalog_id in config.catalog_ids:
        assert isinstance(catalog_id, str)


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_metrics_are_pairs(config_path: Path) -> None:
    config = ViewConfig(config_path)
    for catalog_id, metric_id in config.metrics:
        assert isinstance(catalog_id, str)
        assert isinstance(metric_id, str)


def test_view_config_known_values() -> None:
    config = ViewConfig(TEST_FILES_ROOT / "input_two_hourly" / "view_config.yml")
    assert config.id == "view_area"
    assert config.location_taxonomy_category == "balance"
    assert config.catalog_ids == ["catalog_1"]
    assert ("catalog_1", "OVERALL_COST") in config.metrics
    assert ("catalog_1", "UNSP_ENRG") in config.metrics
    assert ("catalog_1", "MRG_PRICE") in config.metrics


def test_view_config_time_aggregation() -> None:
    config = ViewConfig(TEST_FILES_ROOT / "input_two_hourly" / "view_config.yml")
    assert config.time_aggregation == TimeAggregation.HOURS
