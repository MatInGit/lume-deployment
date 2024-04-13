import mlflow
from mlflow.models.model import get_model_info
from mlflow import MlflowClient
import pandas as pd
import yaml
import sympy as sp
from lume_model.models import TorchModule, TorchModel
from mm.model_utils import ModelGetterBase

from mm.logging_utils import get_logger

logger = get_logger()


class MLflowModelGetter(ModelGetterBase):
    def __init__(self, model_name: str, model_version: str):
        logger.debug(f"MLflowModelGetter: {model_name}, {model_version}")
        self.model_name = model_name
        self.model_version = model_version
        self.client = MlflowClient()
        self.model_type = None
        self.tags = None

    def get_config(self):
        self.get_tags()
        version = self.client.get_model_version(self.model_name, self.model_version)

        if "artifact_location" in self.tags.keys():
            artifact_location = self.tags["artifact_location"]
            logger.debug(f"Artifact location: {artifact_location}")
        else:
            artifact_location = version.name
            logger.debug(f"Artifact location: {artifact_location}")
        self.client.download_artifacts(
            version.run_id, f"{artifact_location}/pv_mapping.yaml", "."
        )
        return yaml.load(
            open(f"{artifact_location}/pv_mapping.yaml", "r"), Loader=yaml.FullLoader
        )

    def get_tags(self):
        registry_model = self.client.get_registered_model(self.model_name)
        self.tags = registry_model.tags

    def get_requirements(self):
        # Get dependencies
        if int(self.model_version) >= 0:
            version = self.client.get_model_version(self.model_name, self.model_version)
        elif self.model_version == "champion":  # this is stupid I need to change it
            version_no = self.client.get_model_version_by_alias(
                self.model_name, self.model_version
            )
            version = self.client.get_model_version(self.model_name, version_no.version)

        deps = mlflow.artifacts.download_artifacts(f"{version.source}/requirements.txt")
        return deps

    def get_model(self):
        self.get_tags()
        version = self.client.get_model_version(self.model_name, self.model_version)

        # flavor
        flavor = get_model_info(model_uri=version.source).flavors
        loader_module = flavor["python_function"]["loader_module"]
        logger.debug(f"Loader module: {loader_module}")

        if loader_module == "mlflow.pyfunc.model":
            logger.debug("Loading pyfunc model")
            model_pyfunc = mlflow.pyfunc.load_model(model_uri=version.source)
            model = model_pyfunc.unwrap_python_model().get_lume_model()
            logger.debug(f"Model: {model}, Model type: {type(model)}")
            self.model_type = "pyfunc"
            return model

        elif loader_module == "mlflow.pytorch":
            print("Loading torch model")
            model_torch_module = mlflow.pytorch.load_model(model_uri=version.source)
            assert isinstance(model_torch_module, TorchModule)
            model = model_torch_module.model
            assert isinstance(model, TorchModel)
            logger.debug(f"Model: {model}, Model type: {type(model)}")
            self.model_type = "torch"
            return model
        else:
            raise Exception(f"Flavor {flavor} not supported")
