# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Command line interface for GEMS-ViewsBuilder."""

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SystemType(Enum):
    DIRECTORY = "directory"
    FILE = "file"


@dataclass
class PathOption:
    name: str
    args_attribute: str = field(init=False)
    system_type: SystemType
    system_check: Callable[[Path], bool]

    def __post_init__(self) -> None:
        self.args_attribute = self.name.replace("-", "_")


def parent_is_dir(path: Path) -> bool:
    parent_dir = path.parent
    return parent_dir != Path(".") and parent_dir.is_dir()


PATHS_OPTIONS: list[PathOption] = [
    PathOption("catalogs-dir", SystemType.DIRECTORY, Path.is_dir),
    PathOption("libraries-dir", SystemType.DIRECTORY, Path.is_dir),
    PathOption("system", SystemType.FILE, Path.is_file),
    PathOption("calendar", SystemType.FILE, Path.is_file),
    PathOption("taxonomy", SystemType.FILE, Path.is_file),
]

MULTIPLE_FILE_PATH_OPTIONS: list[PathOption] = [
    PathOption("simulation-tables", SystemType.DIRECTORY, parent_is_dir),
    PathOption("view-configs", SystemType.DIRECTORY, parent_is_dir),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gems-views-builder",
        description="Build aggregated metric views from a GEMS simulation dataset.",
    )

    add_path_options(parser, PATHS_OPTIONS)
    add_multiple_file_path_options(parser, MULTIPLE_FILE_PATH_OPTIONS)

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Existing directory where the timestamped view result file will be written.",
    )
    parser.add_argument(
        "-f",
        "--output-format",
        dest="output_format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Format of the merged result file (default: parquet).",
    )
    parser.add_argument(
        "-l",
        "--log-dir",
        type=Path,
        help="Directory where the logs will be written.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose console logging.",
    )
    return parser


def add_path_options(parser: argparse.ArgumentParser, options: list[PathOption]) -> None:
    for option in options:
        parser.add_argument(
            f"--{option.name}",
            type=Path,
            required=True,
            help=f"{option.system_type.value} for {option.name}.",
        )


def add_multiple_file_path_options(parser: argparse.ArgumentParser, options: list[PathOption]) -> None:
    for option in options:
        parser.add_argument(
            f"--{option.name}",
            type=str,
            required=True,
            help=f"Multiple file path for {option.name} (e.g. path/st-x-mc-*.parquet).",
        )


def check_paths_options(args: argparse.Namespace) -> None:
    for option in PATHS_OPTIONS:
        # Fetching the value of the option from the parsed args
        option_value = getattr(args, option.args_attribute)
        if not option.system_check(option_value):
            raise OSError(f"--{option.name} : {option_value} is not a {option.system_type.value}")


def check_multiple_file_path_options(args: argparse.Namespace) -> None:
    for option in MULTIPLE_FILE_PATH_OPTIONS:
        # Fetching the value of the option from the parsed args
        option_value = Path(getattr(args, option.args_attribute))
        if not option.system_check(option_value):
            raise OSError(f"--{option.name} : {option_value.parent} is not a {option.system_type.value}")


def check_options(args: argparse.Namespace) -> None:
    check_paths_options(args)
    check_multiple_file_path_options(args)

    if not args.output.is_dir():
        raise NotADirectoryError(f"--output is not a directory: {args.output}")

    if args.log_dir is not None and not args.log_dir.is_dir():
        raise NotADirectoryError(f"Log directory does not exist: {args.log_dir}")
