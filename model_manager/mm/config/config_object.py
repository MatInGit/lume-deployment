import pydantic
from typing import Dict, Any



# all of the below objects need more work
class DeploymentConfig(pydantic.BaseModel):
    type: str


class InputDataConfig(pydantic.BaseModel):
    get_method: str
    config: Any


class InputDataToModelConfig(pydantic.BaseModel):
    input_to_model_transform: str
    config: Any


class ModelToOutputDataConfig(pydantic.BaseModel):
    output_model_to_output_transform: str
    config: Any


class OutputDataToConfig(pydantic.BaseModel):
    put_method: str
    config: Any


class OutputModelConfig(pydantic.BaseModel):
    config: Any

class ConfigObject(pydantic.BaseModel):
    deployment: DeploymentConfig
    input_data: InputDataConfig
    input_data_to_model: InputDataToModelConfig
    output_model_to_data: ModelToOutputDataConfig
    output_data_to: OutputDataToConfig
    outputs_model: OutputModelConfig


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
