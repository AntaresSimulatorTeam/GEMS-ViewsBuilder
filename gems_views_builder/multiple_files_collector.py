# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MultipleFilesCollector:
    """
    Recommended pattern simulation tables: fake_path/output-xxx/st-x-mc-*.parquet
    Recommended pattern view configs: fake_path/view-config-*.yml
    """

    global_pattern: str

    def collect(self) -> list[Path]:
        global_pattern_path = Path(self.global_pattern)
        directory = global_pattern_path.parent
        collected_paths = list(path for path in directory.glob(global_pattern_path.name) if path.is_file())
        if not collected_paths:
            raise FileNotFoundError(f"No files matched global pattern: {global_pattern_path}")
        return collected_paths
