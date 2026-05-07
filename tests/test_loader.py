from pathlib import Path

from gems_views_builder.library import ModelLibrary
from gems_views_builder.loader import Loader
from gems_views_builder.metrics import ViewConfig
from gems_views_builder.simulation_table import SimulationTable
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import Taxonomy


def test_loader_init_has_no_io() -> None:
    """
    Constructor should not touch the filesystem (no glob/yaml/parquet reads).
    """
    missing = Path("/this/path/should/not/exist")
    loader = Loader(missing)
    assert loader.input_data_path == missing


def test_loader_load_into_self_populates_attributes(test_dataset_dir: Path) -> None:
    loader = Loader(test_dataset_dir).load_into_self()

    assert isinstance(loader.system, InputSystem)
    assert isinstance(loader.taxonomy, Taxonomy)
    assert isinstance(loader.view_config, ViewConfig)
    assert isinstance(loader.simulation_table, SimulationTable)
    assert isinstance(loader.model_library, ModelLibrary)


def test_loader_classmethod_load_populates_attributes(test_dataset_dir: Path) -> None:
    loader = Loader.load(test_dataset_dir)

    assert isinstance(loader.system, InputSystem)
    assert isinstance(loader.taxonomy, Taxonomy)
    assert isinstance(loader.view_config, ViewConfig)
    assert isinstance(loader.simulation_table, SimulationTable)
    assert isinstance(loader.model_library, ModelLibrary)
