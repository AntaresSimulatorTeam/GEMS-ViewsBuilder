from pathlib import Path

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
        self.taxonomy = load_taxonomy(self.input_data_path / "taxonomy.yml")
        self.view_config = ViewConfig.load(self.input_data_path / "view_config.yml")
        self.simulation_table = SimulationTable.load(
            next(self.input_data_path.glob("simulation_table*.parquet"))
        )  # # we could have only one simulation table at this phase of development
        self.model_library = ModelLibrary.load(self.input_data_path / "library.yml")
        system_path = next(self.input_data_path.glob("system*"))
        self.system = InputSystem.load(system_path, self.model_library)
        return self
