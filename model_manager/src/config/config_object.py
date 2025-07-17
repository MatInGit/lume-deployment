from typing import Any, Optional, Union
from pydantic import computed_field, model_validator
import pydantic
import networkx as nx
from ..transformers import registered_transformers
from enum import Enum
from matplotlib import pyplot as plt
from uuid import uuid4
import os

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

    @pydantic.field_validator('type')
    def check_type(cls, v):
        if v not in allowed_transformers:
            raise ValueError(
                f'Invalid transformer type: {v}, choose from {allowed_transformers}'
            )
        return v


class ModelToOutputDataConfig(pydantic.BaseModel):
    type: str
    config: Any

    @pydantic.field_validator('type')
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
    
    
class allowedRoutingTypes(Enum):
    in_interface: str = "in_interface"
    in_transformer: str = "in_transformer"
    model: str = "model"
    out_transformer: str = "out_transformer"
    out_interface: str = "out_interface"
    model_evaluator: str = "model_evaluator"
    misc: str = "misc"
    
class RoutingObject(pydantic.BaseModel):
    type: allowedRoutingTypes
    pub: Optional[str] = None
    sub: Optional[str] = None
    args: Optional[dict[str, Union[str, dict, bool]]] | str = None


class RoutingConfig(pydantic.BaseModel):
    config: dict[str, RoutingObject]
    
    class Config:
        arbitrary_types_allowed = True # to allow nx.DiGraph
    
    @computed_field(return_type=nx.DiGraph)
    @property
    def graph(self):
        G = nx.DiGraph()
        # pubs are nodes and subs are edges
        nodes = []
        edges = []
        for key, value in self.config.items():
            nodes.append(value.pub)
            nodes.append(value.sub)
            edges.append((value.sub, value.pub))

        # keep only unique nodes
        nodes = list(set(nodes))
        # remove none values
        nodes = [x for x in nodes if x is not None]
        # remove none values
        edges = [x for x in edges if x[0] is not None and x[1] is not None]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        return G
        
        
    @pydantic.field_validator('graph')
    def check_routing(cls, v):
        isolated_nodes = list(nx.isolates(v))
        if isolated_nodes:
            raise ValueError(
                f'Isolated nodes found in routing graph: {isolated_nodes}'
            )
        return v

class ValidModuleConfig(Enum):
    input_data: InputDataConfig = InputDataConfig
    input_data_to_model: InputDataToModelConfig = InputDataToModelConfig
    output_model_to_data: ModelToOutputDataConfig = ModelToOutputDataConfig
    output_data_to: OutputDataToConfig = OutputDataToConfig
    outputs_model: OutputModelConfig = OutputModelConfig
            

class ConfigObject(pydantic.BaseModel):
    routing: Optional[RoutingConfig] = None
    deployment: DeploymentConfig
    # old 
    # input_data: Optional[dict[str, InputDataConfig]] = None
    # input_data_to_model: Optional[dict[str, InputDataToModelConfig]] = None
    # output_model_to_data: Optional[dict[str, ModelToOutputDataConfig]] = None
    # output_data_to: Optional[dict[str, OutputDataToConfig]] = None
    # outputs_model: Optional[dict[str, OutputModelConfig]] = None
    
    # new all of these ara a module config
    modules: dict[str, ValidModuleConfig]

    
    

    @model_validator(mode='before')
    @classmethod
    def set_default_routing(cls, values):
        if 'routing' not in values:
            values['routing'] = makeDefaultRoutingConfig()
        return values
    
    def draw_routing_graph(self):
        G = self.routing.graph
        plt.figure(figsize=(10, 10))
        nx.draw(G, with_labels=True)
        if not os.path.exists("./graphs"):
            os.makedirs("./graphs")
        plt.savefig("./graphs/{}_routing_graph.png".format(uuid4()))
