import pydantic
from typing import Dict, Any


class DeploymentConfig(pydantic.BaseModel):
    type: str


class InputDataConfig(pydantic.BaseModel):
    get_method: str
    config: Any


class InputDataToModelConfig(pydantic.BaseModel):
    input_to_model_transform: str
    config: Dict[str, Dict[str, str]]


class ModelToOutputDataConfig(pydantic.BaseModel):
    output_model_to_output_transform: str
    config: Dict[str, Dict[str, str]]


class OutputDataToConfig(pydantic.BaseModel):
    put_method: str
    config: Any


class ConfigObject(pydantic.BaseModel):
    deployment: DeploymentConfig
    input_data: InputDataConfig
    input_data_to_model: InputDataToModelConfig
    output_model_to_data: ModelToOutputDataConfig
    output_data_to: OutputDataToConfig


# input_data:
#   get_method: "k2eg"
#   config:
#     intialize: false
#     variables:
#       QUAD:LTUH:680:BCTRL:
#         proto: ca
#         name: QUAD:LTUH:680:BCTRL
#       LUME:MLFLOW:TEST_A:
#         proto: ca
#         name: LUME:MLFLOW:TEST_A
