from collections import defaultdict
from pathlib import Path

EXACT_FILES = ["taxonomy.yml", "view_config.yml", "library.yml", "system.yml"]
PREFIX_FILES = {"calendar": ".csv", "simulation_table": ".parquet"}


class InputValidator:
    """
    Validator of the input data
    """

    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def _check_input_data_path(self) -> None:
        """
        # Check if input_data_path exists and is a directory.
        """
        if not self.input_data_path.is_dir():
            raise NotADirectoryError(f"Input data path {self.input_data_path} is not a directory")

    def _check_catalogs_directory(self) -> None:
        """
        # Check if catalogs directory exists and is a directory.
        # Check if catalogs directory is empty.
        """
        catalogs_path = self.input_data_path / "catalogs"
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.iterdir()):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")  # 1 * constraint

    def _check_required_input_files(self) -> None:
        """
        # Check if there are exactly 6 required files.
        """
        files_counter: defaultdict[str, int] = defaultdict(int)
        # # Check names
        for filename in EXACT_FILES:
            if not (self.input_data_path / filename).is_file():
                raise FileNotFoundError(f"Required file '{filename}' not found in {self.input_data_path}")
            files_counter[filename] += 1

        for prefix, expected_suffix in PREFIX_FILES.items():
            match = next(self.input_data_path.glob(f"{prefix}*"), None)
            if match is None:
                raise FileNotFoundError(f"Required file starting with '{prefix}' not found in {self.input_data_path}")
            if match.suffix != expected_suffix:
                raise ValueError(f"File '{match.name}' starting with '{prefix}' must be a '{expected_suffix}' file")
            files_counter[match.name] += 1

        # # Check counter
        if sum(files_counter.values()) != len(EXACT_FILES) + len(PREFIX_FILES):
            raise ValueError(
                f"Expected {len(EXACT_FILES) + len(PREFIX_FILES)} files in {self.input_data_path}, found {len(files_counter)}"
            )

    def validate(self) -> None:
        """
        Expected files:
        - taxonomy.yml
        - view_config.yml
        - library.yml
        - system.yml
        - simulation_table.parquet
        - calendar.csv
        - catalogs directory with 1 * catalogs without strict name convention for now
        """
        self._check_input_data_path()

        self._check_catalogs_directory()

        self._check_required_input_files()
