from p4p.client.thread import Context
from p4p.server import Server
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV
from p4p.nt import NTScalar

from .BaseInterface import BaseInterface
from mm.logging_utils import get_logger
import os

logger = get_logger()

# os.environ["EPICS_PVA_NAME_SERVERS"] = "localhost:5075"


class SimplePVAInterface(BaseInterface):
    def __init__(self, config):
        self.ctxt = Context("pva", nt=False)
        if "EPICS_PVA_NAME_SERVERS" in os.environ:
            logger.debug(
                f"EPICS_PVA_NAME_SERVERS: {os.environ['EPICS_PVA_NAME_SERVERS']}"
            )
        elif "EPICS_PVA_NAME_SERVERS" in config.config:
            os.environ["EPICS_PVA_NAME_SERVERS"] = config.config[
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

        pv_dict = config.config["variables"]
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
            logger.debug(f"SimplePVAInterface handler for {name, value['value']}")
            handler(name, {"value": float(value["value"])})

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
        return name, self.ctxt.get(name)

    def put(self, name, value, **kwargs):
        return self.ctxt.put(name, value)

    def put_many(self, data, **kwargs):
        pass

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
        self.shared_pvs = []
        for pv in self.pv_list:
            # self.shared_pvs.append(pv)
            pv_item = {}
            pv_item[pv] = SharedPV(nt=NTScalar("d"), initial=0)

            @pv_item[pv].put
            def put(pv: SharedPV, op: ServOpWrap):
                logger.debug(f"Put {pv} {op}")
                pv.post(op.value())
                op.done()

            self.shared_pvs.append(pv_item)
            # this feels ugly

        self.server = Server(providers=self.shared_pvs)

    def close(self):
        logger.debug("Closing SimplePVAInterfaceServer")
        self.server.stop()
        super().close()
