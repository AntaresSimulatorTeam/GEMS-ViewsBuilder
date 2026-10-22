# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
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
    """A valid value for every required option. Each test overrides only the option it is about.

    The CLI only checks paths and patterns, never file contents, so empty files are enough.
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


def parse_and_check(options: dict[str, str]) -> InputPaths:
    args = build_parser().parse_args(to_argv(options))
    check_options(args)
    return InputPaths(args)


# --- Parser ---------------------------------------------------------------------------------------------------------


def test_parser_applies_defaults_for_optional_options(options: dict[str, str]) -> None:
    # Arrange
    argv = to_argv(options)

    # Act
    args = build_parser().parse_args(argv)

    # Assert
    assert args.output_format == "parquet"
    assert args.log_dir is None
    assert args.verbose is False


def test_parser_accepts_short_flags(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    output_dir = tmp_path / "out"
    log_dir = tmp_path / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    del options["--output-dir"]
    argv = to_argv(options) + ["-o", str(output_dir), "-f", "csv", "-l", str(log_dir), "-v"]

    # Act
    args = build_parser().parse_args(argv)

    # Assert
    assert args.output_dir == output_dir
    assert args.output_format == "csv"
    assert args.log_dir == log_dir
    assert args.verbose is True


def test_parser_keeps_glob_patterns_as_raw_strings(options: dict[str, str]) -> None:
    # Arrange
    options["--simulation-tables"] = "output-xxx/st-x-mc-*.parquet"

    # Act
    args = build_parser().parse_args(to_argv(options))

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
    options: dict[str, str], missing_option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    del options[missing_option]
    argv = to_argv(options)
    parser = build_parser()

    # Act
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(argv)

    # Assert
    assert exc_info.value.code == 2
    assert missing_option in capsys.readouterr().err


def test_parser_exits_on_unsupported_output_format(options: dict[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    options["--output-format"] = "json"
    argv = to_argv(options)
    parser = build_parser()

    # Act
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(argv)

    # Assert
    assert exc_info.value.code == 2
    assert "invalid choice: 'json'" in capsys.readouterr().err


# --- Accepted input files: single paths -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("option", "file_name"),
    [("--system", "my-system.yml"), ("--calendar", "my-calendar.csv"), ("--taxonomy", "my-taxonomy.yml")],
)
def test_existing_file_is_accepted(tmp_path: Path, options: dict[str, str], option: str, file_name: str) -> None:
    # Arrange
    input_file = make_file(tmp_path / "inputs" / file_name)
    options[option] = str(input_file)

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert getattr(input_paths, option.removeprefix("--")) == input_file


def test_existing_libraries_directory_is_accepted(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    libraries_dir = tmp_path / "inputs" / "my-libraries"
    library = make_file(libraries_dir / "library.yml")
    options["--libraries-dir"] = str(libraries_dir)

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert input_paths.libraries == [library]


# --- Accepted input files: patterns ---------------------------------------------------------------------------------


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
    tmp_path: Path, options: dict[str, str], pattern: str
) -> None:
    # Arrange
    table = make_file(tmp_path / "inputs" / "simulation_table--20260318-0623.parquet")
    options["--simulation-tables"] = str(tmp_path / "inputs" / pattern)

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert input_paths.simulation_tables == [table]


def test_simulation_tables_pattern_collects_several_monte_carlo_files(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    tables_dir = tmp_path / "output-xxx"
    tables = {make_file(tables_dir / f"st-x-mc-{mc}.parquet") for mc in range(1, 4)}
    options["--simulation-tables"] = str(tables_dir / "st-x-mc-*.parquet")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert set(input_paths.simulation_tables) == tables


def test_view_configs_pattern_collects_several_files(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    files = {make_file(tmp_path / "inputs" / f"file-{index}.yml") for index in range(1, 3)}
    options["--view-configs"] = str(tmp_path / "inputs" / "file-*.yml")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert set(input_paths.view_configs) == files


def test_catalogs_directory_loads_every_yml(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    files = {make_file(tmp_path / "inputs" / f"file-{index}.yml") for index in range(1, 3)}
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert set(input_paths.catalogs) == files


def test_catalogs_directory_ignores_non_yml_files(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    other = make_file(tmp_path / "inputs" / "taxonomy.yml")
    make_file(tmp_path / "inputs" / "catalog-1.yml.bak")
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert set(input_paths.catalogs) == {catalog, other}


def test_catalogs_directory_ignores_directories_named_like_yml(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    (tmp_path / "inputs" / "catalog-2.yml").mkdir(parents=True, exist_ok=True)
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert input_paths.catalogs == [catalog]


def test_catalogs_directory_does_not_search_subdirectories(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    catalog = make_file(tmp_path / "inputs" / "catalog-1.yml")
    make_file(tmp_path / "inputs" / "nested" / "catalog-2.yml")
    options["--catalogs-dir"] = str(tmp_path / "inputs")

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert input_paths.catalogs == [catalog]


# --- Accepted input files: patterns with . and .. -------------------------------------------------------------------


@pytest.mark.parametrize("pattern", ["st-x-mc-*.parquet", "./st-x-mc-*.parquet", "././st-x-mc-*.parquet"])
def test_pattern_in_temp_directory_is_accepted(tmp_path: Path, options: dict[str, str], pattern: str) -> None:
    # Arrange
    inputs = tmp_path / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    table = make_file(inputs / "st-x-mc-1.parquet")
    options["--simulation-tables"] = f"{inputs}/{pattern}"

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert [path.resolve() for path in input_paths.simulation_tables] == [table]


@pytest.mark.parametrize("pattern", ["../st-x-mc-*.parquet", "../../work/st-x-mc-*.parquet"])
def test_pattern_through_parent_directory_is_accepted(tmp_path: Path, options: dict[str, str], pattern: str) -> None:
    # Arrange
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "sub").mkdir(parents=True, exist_ok=True)
    table = make_file(work_dir / "st-x-mc-1.parquet")
    options["--simulation-tables"] = f"{work_dir / 'sub'}/{pattern}"

    # Act
    input_paths = parse_and_check(options)

    # Assert
    assert [path.resolve() for path in input_paths.simulation_tables] == [table]


# --- Wrong pattern --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("option", ["--simulation-tables", "--view-configs"])
def test_pattern_with_missing_parent_directory_is_rejected(
    tmp_path: Path, options: dict[str, str], option: str
) -> None:
    # Arrange
    options[option] = str(tmp_path / "missing" / "*.yml")
    args = build_parser().parse_args(to_argv(options))

    # Act
    with pytest.raises(OSError) as exc_info:
        check_options(args)

    # Assert
    assert exc_info.match(rf"{option} : .*missing.* is not an existing folder")


@pytest.mark.parametrize("option", ["--simulation-tables", "--view-configs"])
def test_pattern_whose_parent_is_a_file_is_rejected(tmp_path: Path, options: dict[str, str], option: str) -> None:
    # Arrange
    not_a_dir = make_file(tmp_path / "inputs.yml")
    options[option] = str(not_a_dir / "*.yml")
    args = build_parser().parse_args(to_argv(options))

    # Act
    with pytest.raises(OSError) as exc_info:
        check_options(args)

    # Assert
    assert exc_info.match(rf"{option} : .*inputs.yml.* is not an existing folder")


def test_pattern_with_wildcard_in_directory_part_is_rejected(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange: only the file name may contain wildcards.
    make_file(tmp_path / "output-1" / "st-x-mc-1.parquet")
    options["--simulation-tables"] = str(tmp_path / "output-*" / "st-x-mc-*.parquet")
    args = build_parser().parse_args(to_argv(options))

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
    tmp_path: Path, options: dict[str, str], option: str, existing_file: str, pattern: str
) -> None:
    # Arrange
    make_file(tmp_path / "inputs" / existing_file)
    options[option] = str(tmp_path / "inputs" / pattern)
    args = build_parser().parse_args(to_argv(options))
    check_options(args)

    # Act
    with pytest.raises(FileNotFoundError) as exc_info:
        InputPaths(args)

    # Assert
    assert exc_info.match("No files matched global pattern")


def test_pattern_in_empty_directory_is_rejected(tmp_path: Path, options: dict[str, str]) -> None:
    # Arrange
    empty = tmp_path / "empty"
    empty.mkdir(parents=True, exist_ok=True)
    options["--view-configs"] = str(empty / "*.yml")
    args = build_parser().parse_args(to_argv(options))
    check_options(args)

    # Act
    with pytest.raises(FileNotFoundError) as exc_info:
        InputPaths(args)

    # Assert
    assert exc_info.match("No files matched global pattern")


@pytest.mark.parametrize("option", ["--system", "--calendar", "--taxonomy"])
def test_file_correct_file_option(tmp_path: Path, options: dict[str, str], option: str) -> None:
    file = make_file(tmp_path / "file.yml")
    options[option] = str(file)
    args = build_parser().parse_args(to_argv(options))

    check_options(args)


@pytest.mark.parametrize("option", ["--system", "--calendar", "--taxonomy"])
def test_raises_when_is_directory_given_instead_of_file(tmp_path: Path, options: dict[str, str], option: str) -> None:
    directory = tmp_path / "a-directory"
    directory.mkdir(parents=True, exist_ok=True)
    options[option] = str(directory)
    args = build_parser().parse_args(to_argv(options))

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
def test_directory_option_is_accepted(tmp_path: Path, options: dict[str, str], option: str, attribute: str) -> None:
    directory = tmp_path / "checked"
    directory.mkdir()
    options[option] = str(directory)
    args = build_parser().parse_args(to_argv(options))

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
    tmp_path: Path, options: dict[str, str], option: str, error: type[OSError], message: str
) -> None:
    path = tmp_path / "not-a-directory"
    path.touch()
    options[option] = str(path)
    args = build_parser().parse_args(to_argv(options))

    with pytest.raises(error) as exc_info:
        check_options(args)

    assert exc_info.match(message)
