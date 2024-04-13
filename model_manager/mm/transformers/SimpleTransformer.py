from mm.logging_utils.make_logger import get_logger
import sympy as sp
import time

logger = get_logger()


class SimpleTransformer:
    def __init__(self, pv_mapping: dict, symbol_list):
        self.pv_mapping = pv_mapping

        for key, value in self.pv_mapping.items():
            self.__validate_formulas(value["formula"])
        self.latest_pvs = {symbol: None for symbol in symbol_list}
        self.latest_transformed = {key: None for key in self.pv_mapping.keys()}
        self.updated = False

        self.handler_time = []

    def __validate_formulas(self, formula: str):
        try:
            sp.sympify(formula.replace(":", "_"))
        except:
            raise Exception(f"Invalid formula: {formula}")

    def handler_for_k2eg(self, pv_name, value):
        # strip protoco; ca:// or pva:// from pv_name if present
        if pv_name.startswith("ca://"):
            pv_name = pv_name[5:]
        elif pv_name.startswith("pva://"):
            pv_name = pv_name[6:]
        else:
            pass

        self.latest_pvs[pv_name] = value["value"]
        # print(self.latest_pvs)
        if all([value is not None for value in self.latest_pvs.values()]):
            # print("All PVs updated")
            self.transform()

    def transform(self):
        transformed = {}
        pvs_renamed = {
            key.replace(":", "_"): value for key, value in self.latest_pvs.items()
        }
        for key, value in self.pv_mapping.items():
            transformed[key] = sp.sympify(value["formula"].replace(":", "_")).subs(
                pvs_renamed
            )

        for key, value in transformed.items():
            self.latest_transformed[key] = value
        self.updated = True
