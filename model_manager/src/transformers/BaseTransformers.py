from src.logging_utils.make_logger import get_logger
import sympy as sp
import numpy as np
import time

logger = get_logger()


class SimpleTransformer:
    def __init__(self, config):
        """
        config: dict
            dictionary containing the following keys:
            - variables: dict
                dictionary containing the following keys:
                - formula: str
                    formula to be used for transformation
            - symbols: list
                list of symbols to be used in the formula
        """

        pv_mapping = config["variables"]
        self.input_list = config["symbols"]

        logger.debug("Initializing SimpleTransformer")
        logger.debug(f"PV Mapping: {pv_mapping}")
        logger.debug(f"Symbol List: {self.input_list}")
        self.pv_mapping = pv_mapping

        for key, value in self.pv_mapping.items():
            self.__validate_formulas(value["formula"])
        self.latest_input = {symbol: None for symbol in self.input_list}
        self.latest_transformed = {key: 0 for key in self.pv_mapping.keys()}
        self.updated = False
        self.handler_time = None

        self.handler_time = []

    def __validate_formulas(self, formula: str):
        try:
            sp.sympify(formula.replace(":", "_"))
        except:
            raise Exception(f"Invalid formula: {formula}")

    def handler(self, pv_name, value):
        # logger.debug(f"SimpleTransformer handler for {pv_name} with value {value}")

        # assert valus is float
        try:
            # logger.debug(f"Converting value to float: {value}")
            # logger.debug(f"Value type: {type(value)}")
            # logger.debug(f"Value: {value['value']}")
            value = float(value["value"])
        except Exception as e:
            logger.error(f"Error converting value to float: {e}")
            raise e

        self.latest_input[pv_name] = value
        try:
            if all([value is not None for value in self.latest_input.values()]):
                time_start = time.time()
                self.transform()
                self.handler_time = time.time() - time_start
        except Exception as e:
            logger.error(f"Error transforming: {e}")
            raise e

    def transform(self):
        # logger.debug("Transforming")
        transformed = {}
        pvs_renamed = {
            key.replace(":", "_"): value for key, value in self.latest_input.items()
        }
        for key, value in self.pv_mapping.items():
            try:
                transformed[key] = sp.sympify(value["formula"].replace(":", "_")).subs(
                    pvs_renamed
                )
                # converted to float
                transformed[key] = float(transformed[key])
            except Exception as e:
                logger.error(f"Error transforming: {e}")
                raise e

        for key, value in transformed.items():
            self.latest_transformed[key] = value
        self.updated = True


class CAImageTransfomer:
    """Input only image transformation"""

    def __init__(self, config) -> None:
        self.img = config["variables"]
        self.img_list = list(self.img.keys())

        self.variables = {}
        self.input_list = []
        for key, value in self.img.items():
            self.variables[key] = value["img_ch"]
            self.variables[key + "_x"] = value["img_x_ch"]
            self.variables[key + "_y"] = value["img_y_ch"]
            self.input_list.append(value["img_ch"])
            self.input_list.append(value["img_x_ch"])
            self.input_list.append(value["img_y_ch"])

        self.latest_input = {symbol: None for symbol in self.input_list}
        self.latest_transformed = {key: 0 for key in self.variables.keys()}

        self.handler_time = None
        self.updated = False

    def handler(self, variable_name: str, value: dict):
        logger.debug(f"CAImageTransfomer handler for {variable_name}")
        # logger.debug(f"Value: {value}")
        try:
            self.latest_input[variable_name] = value["value"]
            if all([value is not None for value in self.latest_input.values()]):
                time_start = time.time()
                self.transform()
                self.handler_time = time.time() - time_start
            else:
                logger.debug("Not all values are present")
        except Exception as e:
            logger.error(f"Error transforming: {e}")
            raise e

    def transform(self):
        logger.debug("Transforming")
        transformed = {}
        for key in self.img_list:
            value = self.latest_input[self.variables[key]]
            # print(f"key: {key}, value: {value}")
            try:
                transformed[key] = np.array(value).reshape(
                    int(self.latest_input[self.variables[key + "_x"]]),
                    int(self.latest_input[self.variables[key + "_y"]]),
                )
            except Exception as e:
                logger.error(f"Error transforming: {e}")
        for key, value in transformed.items():
            self.latest_transformed[key] = value
        self.updated = True


class PassThroughTransformer:
    def __init__(self, config):
        # config is a dictionary of output:intput pairs
        pv_mapping = config["variables"]
        self.latest_input = {}
        self.latest_transformed = {}
        self.updated = False
        self.input_list = list(pv_mapping.values())

        for key, value in pv_mapping.items():
            self.latest_input[value] = None
            self.latest_transformed[key] = None
        self.pv_mapping = pv_mapping

        self.handler_time = 0

    def handler(self, pv_name, value):
        time_start = time.time()
        logger.debug(f"PassThroughTransformer handler for {pv_name}")
        self.latest_input[pv_name] = value["value"]
        if all([value is not None for value in self.latest_input.values()]):
            self.transform()
        self.updated = True
        time_end = time.time()
        self.handler_time = time_end - time_start

    def transform(self):
        logger.debug("Transforming")
        for key, value in self.pv_mapping.items():
            self.latest_transformed[key] = self.latest_input[value]

            # compare types and shapes
            if type(self.latest_input[value]) != type(self.latest_transformed[key]):
                logger.error(f"Type mismatch between input and output for {key}")
            if type(self.latest_input[value]) == np.ndarray:
                if self.latest_input[value].shape != self.latest_transformed[key].shape:
                    logger.error(f"Shape mismatch between input and output for {key}")
        self.updated = True

        # for key, value in self.latest_input.items():
        #     logger.debug(f"{key}: {value.shape}")
        # for key, value in self.latest_transformed.items():
        #     logger.debug(f"{key}: {value.shape}")
