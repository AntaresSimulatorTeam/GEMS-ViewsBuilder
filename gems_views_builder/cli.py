# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Command line interface for GEMS-ViewsBuilder."""

import argparse
import logging
from pathlib import Path

REQUIRED_DIRECTORIES = ["catalogs-dir", "libraries-dir"]
REQUIRED_FILES = ["system", "calendar", "taxonomy", "simulation-table", "view-config"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gems-views-builder",
        description="Build aggregated metric views from a GEMS simulation dataset.",
    )

    add_directory_arguments(parser, REQUIRED_DIRECTORIES)
    add_file_arguments(parser, REQUIRED_FILES)

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


def add_directory_arguments(parser: argparse.ArgumentParser, directory_arguments: list[str]) -> None:
    for directory_argument in directory_arguments:
        parser.add_argument(
            f"--{directory_argument}",
            type=Path,
            required=True,
            help=f"Directory for {directory_argument}.",
        )


def add_file_arguments(parser: argparse.ArgumentParser, file_arguments: list[str]) -> None:
    for file_argument in file_arguments:
        parser.add_argument(
            f"--{file_argument}",
            type=Path,
            required=True,
            help=f"File containing the {file_argument}.",
        )


def _dest_name(option: str) -> str:
    return option.replace("-", "_")


def check_directory_options(directory_options: list[tuple[str, Path]]) -> int | None:
    for option, path in directory_options:
        if not path.is_dir():
            logging.error(f"{option} is not a directory: {path}")
            return 2
    return None


def check_file_options(file_options: list[tuple[str, Path]]) -> int | None:
    for option, path in file_options:
        if not path.is_file():
            logging.error(f"{option} is not a file: {path}")
            return 2
    return None


def check_options(args: argparse.Namespace) -> int | None:
    directory_options = [(f"--{name}", getattr(args, _dest_name(name))) for name in REQUIRED_DIRECTORIES]
    file_options = [(f"--{name}", getattr(args, _dest_name(name))) for name in REQUIRED_FILES]

    if (error := check_directory_options(directory_options)) is not None:
        return error
    if (error := check_file_options(file_options)) is not None:
        return error

    if not args.output.is_dir():
        logging.error(f"--output is not a directory: {args.output}")
        return 2

    if args.log_dir is not None and not args.log_dir.is_dir():
        logging.error(f"Log directory does not exist: {args.log_dir}")
        return 2

    return None
