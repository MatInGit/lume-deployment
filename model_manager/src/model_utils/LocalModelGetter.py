# not implemented yet warning
import importlib.util

from model_manager.src.logging_utils import get_logger
from model_manager.src.model_utils import ModelGetterBase

logger = get_logger()


class LocalModelGetter(ModelGetterBase):
    def __init__(self, config):
        self.model_module_path = config["model_path"]
        self.model_class_name = config["model_factory_class"]
        self.model_type = "local"

    def get_model(self):
        # Import the model class from the specified module
        spec = importlib.util.spec_from_file_location(
            "model_module", self.model_module_path
        )
        model_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_module)
        model_factory_class = getattr(model_module, self.model_class_name)

        # Create an instance of the model factory class
        model_factory = model_factory_class()
        model = model_factory.get_model()
        return model

    def get_requirements(self):
        return self.requirements
