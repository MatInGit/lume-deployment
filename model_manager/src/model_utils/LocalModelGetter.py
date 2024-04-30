# not implemented yet warning
from warnings import warn
import colorlog
from src.model_utils import ModelGetterBase
from src.logging_utils import get_logger

logger = get_logger()


class LocalModelGetter(ModelGetterBase):
    def __init__(self):
        warn("LocalModelGetter is not implemented yet")
        raise NotImplementedError("LocalModelGetter is not implemented yet")

    def get_model(self, model_name: str, model_version: str):
        raise NotImplementedError("LocalModelGetter is not implemented yet")
