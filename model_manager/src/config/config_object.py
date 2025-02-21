from typing import Any, Optional, Union
from pydantic import computed_field, model_validator
import pydantic
import networkx as nx
from ..transformers import registered_transformers
from enum import Enum
from matplotlib import pyplot as plt
from uuid import uuid4
import os
import logging
allowed_transformers = list(registered_transformers.keys())


# # all of the below objects need more work



# class InputDataConfig(pydantic.BaseModel):
#     get_method: str
#     config: Any


# class InputDataToModelConfig(pydantic.BaseModel):
#     type: str
#     config: Any

#     @pydantic.field_validator('type')
#     def check_type(cls, v):
#         if v not in allowed_transformers:
#             raise ValueError(
#                 f'Invalid transformer type: {v}, choose from {allowed_transformers}'
#             )
#         return v


# class ModelToOutputDataConfig(pydantic.BaseModel):
#     type: str
#     config: Any

#     @pydantic.field_validator('type')
#     def check_type(cls, v):
#         if v not in allowed_transformers:
#             raise ValueError(
#                 f'Invalid transformer type: {v}, choose from {allowed_transformers}'
#             )
#         return v


# class OutputDataToConfig(pydantic.BaseModel):
#     put_method: str
#     config: Any


# class OutputModelConfig(pydantic.BaseModel):
#     config: Any
    
    
# class allowedRoutingTypes(Enum):
#     in_interface: str = "in_interface"
#     in_transformer: str = "in_transformer"
#     model: str = "model"
#     out_transformer: str = "out_transformer"
#     out_interface: str = "out_interface"
#     model_evaluator: str = "model_evaluator"
#     misc: str = "misc"
    
# class RoutingObject(pydantic.BaseModel):
#     type: allowedRoutingTypes
#     pub: Optional[str] = None
#     sub: Optional[str] = None
#     args: Optional[dict[str, Union[str, dict, bool]]] | str = None


# class RoutingConfig(pydantic.BaseModel):
#     config: dict[str, RoutingObject]
    
#     class Config:
#         arbitrary_types_allowed = True # to allow nx.DiGraph
    
#     @computed_field(return_type=nx.DiGraph)
#     @property
#     def graph(self):
#         G = nx.DiGraph()
#         # pubs are nodes and subs are edges
#         nodes = []
#         edges = []
#         for key, value in self.config.items():
#             nodes.append(value.pub)
#             nodes.append(value.sub)
#             edges.append((value.sub, value.pub))

#         # keep only unique nodes
#         nodes = list(set(nodes))
#         # remove none values
#         nodes = [x for x in nodes if x is not None]
#         # remove none values
#         edges = [x for x in edges if x[0] is not None and x[1] is not None]
#         G.add_nodes_from(nodes)
#         G.add_edges_from(edges)
#         return G
        
        
#     @pydantic.field_validator('graph')
#     def check_routing(cls, v):
#         isolated_nodes = list(nx.isolates(v))
#         if isolated_nodes:
#             raise ValueError(
#                 f'Isolated nodes found in routing graph: {isolated_nodes}'
#             )
#         return v

# above is legacy code, below is the new simplified version

class ModuleConfig(pydantic.BaseModel):
    name: str
    pub: Optional[str] = None
    sub: Optional[Union[str, list]] = None
    module_args: Optional[Union[dict[str, Union[str, dict, bool]], str]] = None
    config: Any = None # kind of a free for all for now but we can narrow down the specifics later

    @pydantic.field_validator('module_args', mode = "before")
    def validate_module_args(cls, v):
        if isinstance(v, str):
            return {}
        return v

    
class DeploymentConfig(pydantic.BaseModel):
    type: str


class ConfigObject(pydantic.BaseModel):
    deployment: DeploymentConfig
    modules: dict[str, ModuleConfig]
    class Config:
        arbitrary_types_allowed = True # to allow nx.DiGraph
        

    @computed_field(return_type=nx.DiGraph)
    @property
    def graph(self):
        G = nx.DiGraph()
        nodes = []
        edges = []
        # to collect edges we need to go through each item , look at what its publishing and find matching subsribers, this will form an edge
        for key, value in self.modules.items():
            if isinstance(value.pub, str):
                    value.pub = [value.pub]
            if value.pub is not None and value.pub != []:
                for key2, value2 in self.modules.items():
                    if value2.sub is not None:
                        # normalise them all to lists
                        if isinstance(value2.sub, str):
                            value2.sub = [value2.sub]
                            
                        for pub in value.pub:
                            for sub in value2.sub:
                                if pub == sub and value.name != value2.name:
                                    edges.append((
                                        value.name,
                                        value2.name
                                    ))
                                
            nodes.append(value.name)
            
        # logging.debug(f"Nodes: {nodes}")
        # logging.debug(f"Edges: {edges}")
        nodes = list(set(nodes))
        nodes = [x for x in nodes if x is not None]
        edges = [tuple(x) for x in edges]
        
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        isolated_nodes = list(nx.isolates(G))
        logging.debug(f"Isolated nodes: {isolated_nodes}")
        if isolated_nodes:
            raise ValueError(
                f'Isolated nodes found in routing graph: {isolated_nodes}, this means that a modules is niether a publisher or subscriber to any other module'
            )
        return G
    

    
    def draw_routing_graph(self):
        G = self.graph
        plt.figure(figsize=(10, 10))
        nx.draw(G, with_labels=True)
        if not os.path.exists("./graphs"):
            os.makedirs("./graphs")
        plt.savefig("./graphs/{}_routing_graph.png".format(uuid4()))
