import yaml
from .config_object import ConfigObject


class ConfigParser:
    def __init__(self, config_path):
        self.config_path = config_path

    def parse(self):
        with open(self.config_path, "r") as stream:
            try:
                data = yaml.safe_load(stream)
                return ConfigObject(**data)
            except yaml.YAMLError as exc:
                print(exc)
                return None
