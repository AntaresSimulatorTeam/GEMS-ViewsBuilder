# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path


def collect_files(global_pattern: str) -> list[Path]:
    """
    Recommended pattern simulation tables: fake_path/output-xxx/st-x-mc-*.parquet
    Recommended pattern view configs: fake_path/view-config-*.yml
    """

    global_pattern_path = Path(global_pattern)
    directory = global_pattern_path.parent
    collected_paths = list(path for path in directory.glob(global_pattern_path.name) if path.is_file())
    if not collected_paths:
        raise FileNotFoundError(f"No files matched global pattern: {global_pattern_path}")
    return collected_paths
