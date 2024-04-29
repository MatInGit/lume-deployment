from p4p.client.thread import Context
from p4p.server import Server
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV
from p4p.nt import NTScalar, NTNDArray

from .BaseInterface import BaseInterface
from mm.logging_utils import get_logger
import os, time
import numpy as np

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
            os.environ["EPICS_PVA_NAME_SERVERS"] = config[
                "EPICS_PVA_NAME_SERVERS"
            ]
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
        # print(f"Getting {name}")
        value = self.ctxt.get(name)
        return name, value

    def put(self, name, value, **kwargs):
        return self.ctxt.put(name, value)  # not tested

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
            # self.shared_pvs.append(pv)
            # need to check if key exists config["variables"]["pv"]["type"]
            # print(f"config['variables'][pv]: {config['variables'][pv]}")
            if "type" in config["variables"][pv]:
                # print(f"config['variables'][pv]['type']: {config['variables'][pv]['type']}")
                pv_type = config["variables"][pv]["type"]
                if pv_type == "image":
                    x_size = config["variables"][pv]["image_size"]["x"]
                    y_size = config["variables"][pv]["image_size"]["y"]
                    # intialize with zeros
                    intial_value = np.ones((x_size, y_size))
                    pv_type_nt = NTNDArray()
                    pv_type_init = intial_value

            else:
                pv_type_nt = NTScalar("d")
                pv_type_init = 0

            pv_item = {}
            if self.init_pvs:
                pv_item[pv] = SharedPV(nt=pv_type_nt, initial=pv_type_init)
                # logger.debug(f"pv_item[pv]: {pv_item[pv]}")
            else:
                pv_item[pv] = SharedPV(nt=pv_type_nt, initial=None)
                # logger.debug(f"pv_item[pv]: {pv_item[pv]}")

            @pv_item[pv].put
            def put(pv: SharedPV, op: ServOpWrap):
                # logger.debug(f"Put {pv} {op}")
                pv.post(op.value())
                op.done()

            self.shared_pvs[pv] = pv_item[pv]
            # this feels ugly

        self.server = Server(
            providers=[{name: pv} for name, pv in self.shared_pvs.items()]
        )

    def close(self):
        logger.debug("Closing SimplePVAInterfaceServer")
        self.server.stop()
        super().close()

    def put(self, name, value, **kwargs):
        # logger.debug(f"Putting {name} with value {value}")
        self.shared_pvs[name].post(value, timestamp=time.time())

    def get(self, name, **kwargs):
        # print(f"Getting {name}")
        value_raw = self.shared_pvs[name].current().raw

        # print(f"value_raw_type: {type(value_raw.value)}")
        if type(value_raw.value) == np.ndarray:
            value = value_raw.value
            y_size = value_raw.dimension[0].size
            x_size = value_raw.dimension[1].size
            value = value.reshape((x_size, y_size))
        else:
            value = value_raw.value

        # print(f"value: {value}")
        return name, {"value": value}

    def put_many(self, data, **kwargs):
        for key, value in data.items():
            self.put(key, value)
