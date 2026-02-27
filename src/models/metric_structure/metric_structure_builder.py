from gemspy.gems.input_system import InputSystem  # type: ignore[import-not-found]

from models.business_view_config.business_view_configuration import BusinessViewConfiguration


class MetricStructureBuilder:
    def __init__(self, system: InputSystem, business_view_configuration: BusinessViewConfiguration):
        self.business_view_configuration = business_view_configuration
        self.system = system
