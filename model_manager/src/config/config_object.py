from typing import Any

import pydantic

from ..transformers import registered_transformers

allowed_transformers = list(registered_transformers.keys())


# all of the below objects need more work
class DeploymentConfig(pydantic.BaseModel):
    type: str


class InputDataConfig(pydantic.BaseModel):
    get_method: str
    config: Any


class InputDataToModelConfig(pydantic.BaseModel):
    type: str
    config: Any

    @pydantic.validator('type')
    def check_type(cls, v):
        if v not in allowed_transformers:
            raise ValueError(
                f'Invalid transformer type: {v}, choose from {allowed_transformers}'
            )
        return v


class ModelToOutputDataConfig(pydantic.BaseModel):
    type: str
    config: Any

    @pydantic.validator('type')
    def check_type(cls, v):
        if v not in allowed_transformers:
            raise ValueError(
                f'Invalid transformer type: {v}, choose from {allowed_transformers}'
            )
        return v


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
