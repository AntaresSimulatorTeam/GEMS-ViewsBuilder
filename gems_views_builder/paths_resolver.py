# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PathsResolver:
    """
    Recommended pattern catalogs: fake_path/output-xxx/catalog-*.yml
    """

    path_pattern: str

    def resolve(self) -> list[Path]:
        glob_path = Path(self.path_pattern)
        directory = glob_path.parent
        if not directory.is_dir():
            raise NotADirectoryError(f"Directory does not exist: {directory}")

        resolved_paths = list(path for path in directory.glob(glob_path.name) if path.is_file())
        if not resolved_paths:
            raise FileNotFoundError(f"No files matched pattern: {glob_path}")
        return resolved_paths
