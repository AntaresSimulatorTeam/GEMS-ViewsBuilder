import logging
from pathlib import Path

from gems_views_builder.catalog import load_catalogs
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics import ViewConfig
from gems_views_builder.simulation_table import SimulationTable
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import load_taxonomy


class Loader:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    @classmethod
    def load(cls, input_data_path: Path) -> "Loader":
        """Create a loader and perform all input data I/O."""
        return cls(input_data_path).load_into_self()

    def load_into_self(self) -> "Loader":
        """Perform all input data I/O and populate attributes."""
        logging.info(f"Loading inputs from {self.input_data_path}")
        self.taxonomy = load_taxonomy(self.input_data_path / "taxonomy.yml")
        logging.info("Taxonomy loaded")
        self.view_config = ViewConfig.load(self.input_data_path / "view_config.yml")
        logging.info("View config loaded")
        self.catalogs = load_catalogs(self.input_data_path, self.view_config.catalog_ids)
        logging.info("Catalogs loaded")
        self.simulation_table = SimulationTable.load(
            next(self.input_data_path.glob("simulation_table*.parquet"))
        )  # # we could have only one simulation table at this phase of development
        logging.info("Simulation table loaded")
        self.model_library = ModelLibrary.load(
            self.input_data_path / "library.yml"
        )  # # must be named like this for now, in future when we enable user to have more than one libraries we should decide pattern to use
        logging.info("Model library loaded")
        self.system = InputSystem.from_file(self.input_data_path / "system.yml")
        logging.info(f"System loaded from {self.input_data_path / 'system.yml'}")
        logging.info("All inputs loaded successfully")
        return self

    def _load_system(self) -> InputSystem:
        logging.info("Loading system")
        system_path = next(self.input_data_path.glob("system*"))
        logging.info(f"System loaded from {system_path}")
        return InputSystem.from_file(system_path)
