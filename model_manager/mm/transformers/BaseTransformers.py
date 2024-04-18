from mm.logging_utils.make_logger import get_logger
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

        time

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
            except Exception as e:
                logger.error(f"Error transforming: {e}")
                raise e

        for key, value in transformed.items():
            self.latest_transformed[key] = value
        self.updated = True


class CAImageTransfomer:
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
        logger.debug(
            f"CAImageTransfomer handler for {variable_name} with value {value}"
        )
        try:
            self.latest_input[variable_name] = value["value"]
            if all([value is not None for value in self.latest_input.values()]):
                time_start = time.time()
                self.transform()
                self.handler_time = time.time() - time_start
        except Exception as e:
            logger.error(f"Error transforming: {e}")
            raise e

    def transform(self):
        logger.debug("Transforming")
        transformed = {}
        for key in self.img_list:
            value = self.latest_input[self.variables[key]]
            print(f"key: {key}, value: {value}")
            transformed[key] = np.array(value).reshape(
                self.latest_input[self.variables[key + "_x"]],
                self.latest_input[self.variables[key + "_y"]],
            )
        for key, value in transformed.items():
            self.latest_transformed[key] = value
            print(f"key: {key}, value: {value}")
        self.updated = True
