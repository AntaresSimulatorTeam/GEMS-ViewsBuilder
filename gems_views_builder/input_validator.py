from pathlib import Path

from gems_views_builder.common import logger

EXACT_FILES = ["taxonomy.yml", "view_config.yml", "library.yml", "system.yml"]
PREFIX_FILES = {"calendar": ".csv", "simulation_table": ".parquet"}


class InputValidator:
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

    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def _check_input_data_path(self) -> None:
        """
        # Check if input_data_path exists and is a directory.
        """
        logger.info(f"Validating input directory {self.input_data_path}")
        if not self.input_data_path.is_dir():
            raise NotADirectoryError(f"Input data path {self.input_data_path} is not a directory")
        logger.info(f"Input directory exists: {self.input_data_path}")

    def _check_catalogs_directory(self) -> None:
        """
        # Check if catalogs directory exists and is a directory.
        # Check if catalogs directory is empty.
        """
        catalogs_path = self.input_data_path / "catalogs"
        logger.info(f"Validating catalogs directory {catalogs_path}")
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.iterdir()):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")  # 1 * constraint
        logger.info(f"Catalogs directory is ready: {catalogs_path}")

    def _check_required_input_files(self) -> None:
        """
        # Check if there are exactly 6 required files.
        """
        logger.info(f"Checking required input files in {self.input_data_path}")
        # # Check names
        for filename in EXACT_FILES:
            logger.info(f"Checking presence of required file {filename}")
            if not (self.input_data_path / filename).is_file():
                raise FileNotFoundError(f"Required file '{filename}' not found in {self.input_data_path}")

        for prefix, expected_suffix in PREFIX_FILES.items():
            logger.info(f"Checking presence of file with prefix {prefix!r}")
            matches = list(self.input_data_path.glob(f"{prefix}*"))
            if not matches:
                raise FileNotFoundError(f"Required file starting with '{prefix}' not found in {self.input_data_path}")
            if len(matches) > 1:
                names = ", ".join(sorted(m.name for m in matches))
                raise ValueError(
                    f"Expected exactly one file starting with '{prefix}' in {self.input_data_path}, found: {names}"
                )
            match = matches[0]
            if match.suffix != expected_suffix:
                raise ValueError(f"File '{match.name}' starting with '{prefix}' must be a '{expected_suffix}' file")
            logger.info(f"Found {match.name} for prefix {prefix!r}")

    def validate(self) -> None:
        logger.info(f"Starting input validation for {self.input_data_path}")
        self._check_input_data_path()

        self._check_catalogs_directory()

        self._check_required_input_files()
        logger.info(f"Input validation completed successfully for {self.input_data_path}")
