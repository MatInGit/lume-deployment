from lume_model.base import LUMEBaseModel

import numpy as np

class ExampleModel(LUMEBaseModel):
    def evaluate(self, input_dict):
        output_dict = {}
        output_dict["y"] = np.max([input_dict["x1"], input_dict["x2"]])
        return output_dict
