# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import argparse
from pathlib import Path

import pytest

from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.input_paths import InputPaths


def make_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


@pytest.fixture
def options(tmp_path: Path) -> dict[str, str]:
    """
    A valid value for every required option. Each test overrides only the option it is about.
    """
    libraries = tmp_path / "libraries"
    catalogs = tmp_path / "catalogs"
    output = tmp_path / "output"
    libraries.mkdir()
    catalogs.mkdir()
    output.mkdir()
    system = tmp_path / "system.yml"
    calendar = tmp_path / "calendar.csv"
    taxonomy = tmp_path / "taxonomy.yml"
    simulation_tables = tmp_path / "simulation_table.parquet"
    view_configs = tmp_path / "view_config.yml"
    for path in (
        libraries / "library.yml",
        catalogs / "catalog.yml",
        system,
        calendar,
        taxonomy,
        simulation_tables,
        view_configs,
    ):
        path.touch()
    return {
        "--libraries-dir": str(libraries),
        "--catalogs-dir": str(catalogs),
        "--system": str(system),
        "--calendar": str(calendar),
        "--taxonomy": str(taxonomy),
        "--simulation-tables": str(simulation_tables),
        "--view-configs": str(view_configs),
        "--output-dir": str(output),
    }


def to_argv(options: dict[str, str]) -> list[str]:
    return [token for option, value in options.items() for token in (option, value)]


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    return build_parser()


def parse_and_check(parser: argparse.ArgumentParser, options: dict[str, str]) -> InputPaths:
    args = parser.parse_args(to_argv(options))
    check_options(args)
    return InputPaths(args)


# Parser
def test_parser_applies_defaults_for_optional_options(parser: argparse.ArgumentParser, options: dict[str, str]) -> None:
    # Arrange
    argv = to_argv(options)

    # Act
    args = parser.parse_args(argv)

    # Assert
    assert args.output_format == "parquet"
    assert args.log_dir is None
    assert args.verbose is False


def test_parser_accepts_short_flags(parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    output_dir = tmp_path / "out"
    log_dir = tmp_path / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    del options["--output-dir"]
    argv = to_argv(options) + ["-o", str(output_dir), "-f", "csv", "-l", str(log_dir), "-v"]

    # Act
    args = parser.parse_args(argv)

    # Assert
    assert args.output_dir == output_dir
    assert args.output_format == "csv"
    assert args.log_dir == log_dir
    assert args.verbose is True


def test_parser_keeps_glob_patterns_as_raw_strings(parser: argparse.ArgumentParser, options: dict[str, str]) -> None:
    # Arrange
    options["--simulation-tables"] = "output-xxx/st-x-mc-*.parquet"

    # Act
    args = parser.parse_args(to_argv(options))

    # Assert
    assert args.simulation_tables == "output-xxx/st-x-mc-*.parquet"


@pytest.mark.parametrize(
    "missing_option",
    [
        "--libraries-dir",
        "--system",
        "--calendar",
        "--taxonomy",
        "--simulation-tables",
        "--view-configs",
        "--catalogs-dir",
        "--output-dir",
    ],
)
def test_parser_exits_when_required_option_is_missing(
    parser: argparse.ArgumentParser,
    options: dict[str, str],
    missing_option: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    del options[missing_option]
    argv = to_argv(options)

    with pytest.raises(SystemExit):
        parser.parse_args(argv)

    assert missing_option in capsys.readouterr().err


def test_parser_exits_on_unsupported_output_format(
    parser: argparse.ArgumentParser, options: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    options["--output-format"] = "json"
    argv = to_argv(options)

    with pytest.raises(SystemExit):
        parser.parse_args(argv)

    assert "invalid choice: 'json'" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("option", "file_name"),
    [("--system", "my-system.yml"), ("--calendar", "my-calendar.csv"), ("--taxonomy", "my-taxonomy.yml")],
)
def test_pass_when_file_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str, file_name: str
) -> None:
    # Arrange
    input_file = make_file(tmp_path / file_name)
    options[option] = str(input_file)

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert getattr(input_paths, option.removeprefix("--")) == input_file


def test_existing_libraries_directory_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    libraries_dir = tmp_path / "inputs" / "my-libraries"
    library = make_file(libraries_dir / "library.yml")
    options["--libraries-dir"] = str(libraries_dir)

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert input_paths.libraries == [library]


def test_raises_when_directory_is_not_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    options["--libraries-dir"] = str(tmp_path / "not-a-directory.txt")
    with pytest.raises(OSError):
        parse_and_check(parser, options)


# Test global patterns
@pytest.mark.parametrize(
    "pattern",
    [
        "simulation_table--20260318-0623.parquet",
        "simulation_table*.parquet",
        "simulation_table--*.parquet",
        "simulation_table--20260318-*.parquet",
        "*.parquet",
    ],
)
def test_simulation_tables_pattern_variants_match_the_file(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], pattern: str
) -> None:
    # Arrange
    table = make_file(tmp_path / "inputs" / "simulation_table--20260318-0623.parquet")
    options["--simulation-tables"] = str(tmp_path / "inputs" / pattern)

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert input_paths.simulation_tables == [table]


def test_pass_when_view_configs_pattern_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    files = {make_file(tmp_path / "inputs" / f"view-config-{index}.yml") for index in range(1, 3)}
    options["--view-configs"] = str(tmp_path / "inputs" / "view-config-*.yml")

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert set(input_paths.view_configs) == files


def test_pass_when_catalogs_directory_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    files = {make_file(tmp_path / "inputs" / f"catalog-{index}.yml") for index in range(1, 3)}
    options["--catalogs-dir"] = str(tmp_path / "catalogs")

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert set(input_paths.catalogs) == files


def test_catalogs_directory_ignores_non_yml_files(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # TODO: remove check for file extension
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    other = make_file(tmp_path / "inputs" / "taxonomy.yml")
    make_file(tmp_path / "inputs" / "catalog-1.yml.bak")
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert set(input_paths.catalogs) == {catalog, other}


def test_catalogs_directory_ignores_directories_named_like_yml(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    (tmp_path / "inputs" / "catalog-2.yml").mkdir(parents=True, exist_ok=True)
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert input_paths.catalogs == [catalog]


def test_catalogs_directory_does_not_search_subdirectories(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    make_file(tmp_path / "inputs" / "nested" / "catalog-2.yml")
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert input_paths.catalogs == [catalog]


# --- Accepted input files: patterns with . and .. -------------------------------------------------------------------


@pytest.mark.parametrize("pattern", ["st-x-mc-*.parquet", "./st-x-mc-*.parquet", "././st-x-mc-*.parquet"])
def test_pattern_in_temp_directory_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], pattern: str
) -> None:
    # Arrange
    inputs = tmp_path / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    table = make_file(inputs / "st-x-mc-1.parquet")
    options["--simulation-tables"] = f"{inputs}/{pattern}"

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert [path.resolve() for path in input_paths.simulation_tables] == [table]


@pytest.mark.parametrize("pattern", ["../st-x-mc-*.parquet", "../../work/st-x-mc-*.parquet"])
def test_pattern_through_parent_directory_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], pattern: str
) -> None:
    # Arrange
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "sub").mkdir(parents=True, exist_ok=True)
    table = make_file(work_dir / "st-x-mc-1.parquet")
    options["--simulation-tables"] = f"{work_dir / 'sub'}/{pattern}"

    # Act
    input_paths = parse_and_check(parser, options)

    # Assert
    assert [path.resolve() for path in input_paths.simulation_tables] == [table]


# --- Wrong pattern --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("option", ["--simulation-tables", "--view-configs"])
def test_pattern_with_missing_parent_directory_is_rejected(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str
) -> None:
    # Arrange
    options[option] = str(tmp_path / "missing" / "*.yml")
    args = parser.parse_args(to_argv(options))

    # Act
    with pytest.raises(OSError) as exc_info:
        check_options(args)

    # Assert
    assert exc_info.match(rf"{option} : .*missing.* is not an existing folder")


@pytest.mark.parametrize("option", ["--simulation-tables", "--view-configs"])
def test_pattern_whose_parent_is_a_file_is_rejected(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str
) -> None:
    # Arrange
    not_a_dir = make_file(tmp_path / "inputs.yml")
    options[option] = str(not_a_dir / "*.yml")
    args = parser.parse_args(to_argv(options))

    # Act
    with pytest.raises(OSError) as exc_info:
        check_options(args)

    # Assert
    assert exc_info.match(rf"{option} : .*inputs.yml.* is not an existing folder")


def test_pattern_with_wildcard_in_directory_part_is_rejected(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange: only the file name may contain wildcards.
    make_file(tmp_path / "output-1" / "st-x-mc-1.parquet")
    options["--simulation-tables"] = str(tmp_path / "output-*" / "st-x-mc-*.parquet")
    args = parser.parse_args(to_argv(options))

    # Act
    with pytest.raises(OSError) as exc_info:
        check_options(args)

    # Assert
    assert exc_info.match(r"--simulation-tables : .*output-\*.* is not an existing folder")


@pytest.mark.parametrize(
    ("option", "existing_file", "pattern"),
    [
        ("--simulation-tables", "st-x-mc-1.csv", "st-x-mc-*.parquet"),
        ("--simulation-tables", "simulation_table.parquet", "st-x-mc-*.parquet"),
        ("--view-configs", "view_config.yaml", "view_config*.yml"),
    ],
)
def test_pattern_matching_no_file_is_rejected(
    parser: argparse.ArgumentParser,
    tmp_path: Path,
    options: dict[str, str],
    option: str,
    existing_file: str,
    pattern: str,
) -> None:
    # Arrange
    make_file(tmp_path / "inputs" / existing_file)
    options[option] = str(tmp_path / "inputs" / pattern)
    args = parser.parse_args(to_argv(options))
    check_options(args)

    # Act
    with pytest.raises(FileNotFoundError) as exc_info:
        InputPaths(args)

    # Assert
    assert exc_info.match("No files matched global pattern")


def test_pattern_in_empty_directory_is_rejected(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str]
) -> None:
    # Arrange
    empty = tmp_path / "empty"
    empty.mkdir(parents=True, exist_ok=True)
    options["--view-configs"] = str(empty / "*.yml")
    args = parser.parse_args(to_argv(options))
    check_options(args)

    # Act
    with pytest.raises(FileNotFoundError) as exc_info:
        InputPaths(args)

    # Assert
    assert exc_info.match("No files matched global pattern")


@pytest.mark.parametrize("option", ["--system", "--calendar", "--taxonomy"])
def test_file_correct_file_option(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str
) -> None:
    file = make_file(tmp_path / "file.yml")
    options[option] = str(file)
    args = parser.parse_args(to_argv(options))

    check_options(args)


@pytest.mark.parametrize("option", ["--system", "--calendar", "--taxonomy"])
def test_raises_when_is_directory_given_instead_of_file(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str
) -> None:
    directory = tmp_path / "a-directory"
    directory.mkdir(parents=True, exist_ok=True)
    options[option] = str(directory)
    args = parser.parse_args(to_argv(options))

    with pytest.raises(OSError) as exc_info:
        check_options(args)

    assert exc_info.match(f"{option} is not a file")


@pytest.mark.parametrize(
    ("option", "attribute"),
    [
        ("--libraries-dir", "libraries_dir"),
        ("--catalogs-dir", "catalogs_dir"),
        ("--output-dir", "output_dir"),
        ("--log-dir", "log_dir"),
    ],
)
def test_directory_option_is_accepted(
    parser: argparse.ArgumentParser, tmp_path: Path, options: dict[str, str], option: str, attribute: str
) -> None:
    directory = tmp_path / "checked"
    directory.mkdir()
    options[option] = str(directory)
    args = parser.parse_args(to_argv(options))

    check_options(args)

    assert getattr(args, attribute) == directory


@pytest.mark.parametrize(
    ("option", "error", "message"),
    [
        ("--libraries-dir", OSError, "--libraries-dir is not a directory"),
        ("--catalogs-dir", OSError, "--catalogs-dir is not a directory"),
        ("--output-dir", NotADirectoryError, "--output-dir is not a directory"),
        ("--log-dir", NotADirectoryError, "Log directory does not exist"),
    ],
)
def test_directory_option_is_rejected(
    parser: argparse.ArgumentParser,
    tmp_path: Path,
    options: dict[str, str],
    option: str,
    error: type[OSError],
    message: str,
) -> None:
    path = tmp_path / "not-a-directory"
    path.touch()
    options[option] = str(path)
    args = parser.parse_args(to_argv(options))

    with pytest.raises(error) as exc_info:
        check_options(args)

    assert exc_info.match(message)
