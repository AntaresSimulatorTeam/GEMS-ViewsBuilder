# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.common import configure_logging


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging() -> None:
    """Configure logging once for the whole test session (file + console handlers)."""
    configure_logging()
