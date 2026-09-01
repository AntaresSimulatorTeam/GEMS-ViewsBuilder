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
    FILES = "files"


@dataclass
class Option:
    name: str
    system_type: SystemType
    args_attribute: str = field(init=False)

    def __post_init__(self) -> None:
        self.args_attribute = self.name.replace("-", "_")


@dataclass
class PathOption(Option):
    system_check: Callable[[Path], bool]


@dataclass
class GlobalPatternMatchingOption(Option): ...


REQUIRED_PATHS_OPTIONS: list[PathOption] = [
    PathOption("catalogs-dir", SystemType.DIRECTORY, Path.is_dir),
    PathOption("libraries-dir", SystemType.DIRECTORY, Path.is_dir),
    PathOption("system", SystemType.FILE, Path.is_file),
    PathOption("calendar", SystemType.FILE, Path.is_file),
    PathOption("taxonomy", SystemType.FILE, Path.is_file),
    PathOption("view-config", SystemType.FILE, Path.is_file),
]

GLOBAL_PATTERN_MATCHING_OPTIONS: list[GlobalPatternMatchingOption] = [
    GlobalPatternMatchingOption("simulation-tables", SystemType.FILES),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gems-views-builder",
        description="Build aggregated metric views from a GEMS simulation dataset.",
    )

    add_path_options(parser, REQUIRED_PATHS_OPTIONS)
    add_global_pattern_matching_options(parser, GLOBAL_PATTERN_MATCHING_OPTIONS)

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


def add_path_options(parser: argparse.ArgumentParser, path_options: list[PathOption]) -> None:
    for option in path_options:
        parser.add_argument(
            f"--{option.name}",
            type=Path,
            required=True,
            help=f"{option.system_type.value} for {option.name}.",
        )


def add_global_pattern_matching_options(
    parser: argparse.ArgumentParser, global_pattern_matching_options: list[GlobalPatternMatchingOption]
) -> None:
    for option in global_pattern_matching_options:
        parser.add_argument(
            f"--{option.name}",
            type=str,
            required=True,
            help=f"Global pattern matching for {option.name} (e.g. path/st-x-mc-*.parquet).",
        )


def check_paths_options(args: argparse.Namespace) -> None:
    for option in REQUIRED_PATHS_OPTIONS:
        option_value = getattr(args, option.args_attribute)
        if not option.system_check(option_value):
            raise OSError(f"--{option.name} is not a {option.system_type.value}: {option_value}")


def check_options(args: argparse.Namespace) -> None:
    check_paths_options(args)

    if not args.output.is_dir():
        raise NotADirectoryError(f"--output is not a directory: {args.output}")

    if args.log_dir is not None and not args.log_dir.is_dir():
        raise NotADirectoryError(f"Log directory does not exist: {args.log_dir}")
