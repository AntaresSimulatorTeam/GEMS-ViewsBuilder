from gemspy.gems.input_system import InputSystem

from models.business_view_config.business_view_configuration import BusinessViewConfiguration
from models.business_view_config.calendar import Calendar
from models.common.simulation_table import SimulationTable


class BusinessViewBuilder:
    def __init__(
        self,
        system: InputSystem,
        calendar: Calendar,
        simulation_table: SimulationTable,
        business_view_configuration: BusinessViewConfiguration,
    ):
        self.system = system
        self.calendar = calendar
        self.simulation_table = simulation_table
        self.business_view_configuration = business_view_configuration

    def build_view(self):
        pass
