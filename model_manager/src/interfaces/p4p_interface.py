from p4p.client.thread import Context
from p4p.server import Server, StaticProvider
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV
from p4p.nt import NTScalar, NTNDArray
from p4p.wrapper import Value, Type

import threading

from .BaseInterface import BaseInterface
from src.logging_utils import get_logger
import os, time
import numpy as np

# anyScalar


import warnings

logger = get_logger()

# os.environ["EPICS_PVA_NAME_SERVERS"] = "localhost:5075"


class SimplePVAInterface(BaseInterface):
    def __init__(self, config):
        self.ctxt = Context("pva", nt=False)
        if "EPICS_PVA_NAME_SERVERS" in os.environ:
            logger.debug(
                f"EPICS_PVA_NAME_SERVERS: {os.environ['EPICS_PVA_NAME_SERVERS']}"
            )
        elif "EPICS_PVA_NAME_SERVERS" in config:
            os.environ["EPICS_PVA_NAME_SERVERS"] = config["EPICS_PVA_NAME_SERVERS"]
            logger.debug(
                f"EPICS_PVA_NAME_SERVERS: {os.environ['EPICS_PVA_NAME_SERVERS']}"
            )
        else:
            logger.warning(
                "EPICS_PVA_NAME_SERVERS not set in config or environment, using localhost:5075"
            )
            os.environ["EPICS_PVA_NAME_SERVERS"] = "localhost:5075"

        pv_dict = config["variables"]
        pv_list = []
        for pv in pv_dict:
            try:
                assert pv_dict[pv]["proto"] == "pva"
            except Exception as e:
                logger.error(f"Protocol for {pv} is not pva")
                raise AssertionError
            pv_list.append(pv_dict[pv]["name"])
        self.pv_list = pv_list
        self.variable_list = list(pv_dict.keys())
        logger.debug(f"SimplePVAInterface initialized with pv_url_list: {self.pv_list}")

    def __handler_wrapper(self, handler, name):
        # unwrap p4p.Value into name, value
        def wrapped_handler(value):
            # logger.debug(f"SimplePVAInterface handler for {name, value['value']}")

            handler(name, {"value": value["value"]})

        return wrapped_handler

    def monitor(self, handler, **kwargs):
        for pv in self.pv_list:
            try:
                new_handler = self.__handler_wrapper(handler, pv)
                self.ctxt.monitor(pv, new_handler)
            except Exception as e:
                logger.error(
                    f"Error monitoring in function monitor for SimplePVAInterface: {e}"
                )
                logger.error(f"pv: {pv}")
                raise e

    def get(self, name, **kwargs):
        value = self.ctxt.get(name)
        if type(value["value"]) == np.ndarray:
            # if value has dimension
            if "dimension" in value:
                y_size = value["dimension"][0]["size"]
                x_size = value["dimension"][1]["size"]
                value = value["value"].reshape((y_size, x_size))
            else:
                value = value["value"]
        else:
            value = value["value"]

        value = {"value": value}
        return name, value

    def put(self, name, value, **kwargs):
        if type(value) == np.ndarray:
            value = NTNDArray().wrap(value)
        else:
            value = value
        return self.ctxt.put(name, value)

    def put_many(self, data, **kwargs):
        for key, value in data.items():
            self.put(key, value)

    def get_many(self, data, **kwargs):
        pass

    def close(self):
        logger.debug("Closing SimplePVAInterface")
        self.ctxt.close()


class SimlePVAInterfaceServer(SimplePVAInterface):
    """
    Simple PVA integfcae with a server rather than just a client, this will host the PVs provided in the config
    """

    def __init__(self, config):
        super().__init__(config)
        self.shared_pvs = {}
        pv_type_init = None
        pv_type_nt = None

        if "init" in config:
            # print(f"config['init']: {config['init']}")
            if config["init"] == False:
                self.init_pvs = False
            else:
                self.init_pvs = True
        else:
            self.init_pvs = True

        # print(f"self.init_pvs: {self.init_pvs}")

        for pv in self.pv_list:

            if "type" in config["variables"][pv]:

                pv_type = config["variables"][pv]["type"]
                if pv_type == "image":
                    # note the y and x are flipped when reshaping (rows, columns) -> (y, x)
                    y_size = config["variables"][pv]["image_size"]["y"]
                    x_size = config["variables"][pv]["image_size"]["x"]
                    # intialize with ones
                    intial_value = np.zeros((y_size, x_size))
                    pv_type_nt = NTNDArray()
                    pv_type_init = intial_value

                # waveform
                if pv_type == "waveform":
                    if "length" in config["variables"][pv]:
                        length = config["variables"][pv]["length"]
                    else:
                        length = 10
                    intial_value = np.zeros(length, dtype=np.float64)
                    pv_type_nt = NTScalar("ad")
                    pv_type_nt_bd = NTScalar.buildType("ad")
                    # pv_type_init = Value(pv_type_nt_bd, {"value": intial_value})
                    pv_type_init = intial_value
                    print(f"pv_type_init: {pv_type_init}")
                    

            else:
                warnings.warn(f"No type specified for {pv}")
                pv_type_nt = NTScalar("d")
                pv_type_init = 0
            

            pv_item = {pv: SharedPV(initial=pv_type_init, nt=pv_type_nt)}

            @pv_item[pv].put
            def put(pv: SharedPV, op: ServOpWrap):
                # logger.debug(f"Put {pv} {op}")
                # logger.debug(f"type(pv): {type(op.value())}")
                pv.post(op.value())
                op.done()

            self.shared_pvs[pv] = pv_item[pv]
            # this feels ugly

        # self.server = Server(
        #     providers=[{name: pv} for name, pv in self.shared_pvs.items()]
        # )
        # self.providers = [{name: pv} for name, pv in self.shared_pvs.items()]
        self.provider = StaticProvider("pva")
        for name, pv in self.shared_pvs.items():
            self.provider.add(name, pv)
        
        self.server = Server(providers=[self.provider])

    def close(self):
        logger.debug("Closing SimplePVAInterfaceServer")
        self.server.stop()
        super().close()

    def put(self, name, value, **kwargs):
        logger.info(f"Putting {name} with value {value}")
        # if type(value) == np.ndarray:
        #     value = value.T # quick fix for the fact that the image is flipped
        # print(f"Putting {name} with value {value}")
        self.shared_pvs[name].post(value, timestamp=time.time())

    def get(self, name, **kwargs):
        # print(f"Getting {name}")
        value_raw = self.shared_pvs[name].current().raw
        if type(value_raw.value) == np.ndarray:
            print(f"value_raw_type: {type(value_raw.value)}")
            print(f"value_raw: {value_raw.value}")
            print(f"value_raw_shape: {value_raw.value.shape}")
            # ndtndarray has property dimension
            if "dimension" in value_raw:
                y_size = value_raw.dimension[0]["size"]
                x_size = value_raw.dimension[1]["size"]
                value = value_raw.value.reshape((y_size, x_size))
            else:
                value = value_raw.value
                
        elif type(value_raw.value) == float or type(value_raw.value) == int or type(value_raw.value) == bool:
            value = value_raw.value

        else:
            raise ValueError(f"Unknown type for value_raw: {type(value_raw.value)}")
        # print(f"value: {value}")
        return name, {"value": value}

    def put_many(self, data, **kwargs):
        for key, value in data.items():
            self.put(key, value)
