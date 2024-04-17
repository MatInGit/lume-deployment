from mm.logging_utils.make_logger import get_logger
import sympy as sp
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
        symbol_list = config["symbols"]

        logger.debug("Initializing SimpleTransformer")
        logger.debug(f"PV Mapping: {pv_mapping}")
        logger.debug(f"Symbol List: {symbol_list}")
        self.pv_mapping = pv_mapping

        for key, value in self.pv_mapping.items():
            self.__validate_formulas(value["formula"])
        self.latest_pvs = {symbol: None for symbol in symbol_list}
        self.latest_transformed = {key: 0 for key in self.pv_mapping.keys()}
        self.updated = False

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

        self.latest_pvs[pv_name] = value
        try:
            if all([value is not None for value in self.latest_pvs.values()]):
                self.transform()
        except Exception as e:
            logger.error(f"Error transforming: {e}")
            raise e

    def transform(self):
        # logger.debug("Transforming")
        transformed = {}
        pvs_renamed = {
            key.replace(":", "_"): value for key, value in self.latest_pvs.items()
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
    def __init__(self) -> None:
        pass
