from lume_model.base import LUMEBaseModel

import numpy as np


class ExampleModel(LUMEBaseModel):
    def evaluate(self, input_dict):
        output_dict = {}
        output_dict["y"] = np.max([input_dict["x1"], input_dict["x2"]])
        return output_dict


class ExampleImageModel:
    def evaluate(self, input_dict):
        output_dict = {}
        # input will contain an image (np.array), we want to return the image
        output_dict["y_max"] = np.max(input_dict["image"])
        output_dict["y_min"] = np.min(input_dict["image"])
        output_dict["y_mean"] = np.mean(input_dict["image"])
        output_dict["y_std"] = np.std(input_dict["image"])
        output_dict["y_img"] = input_dict["image"]
        
        # square
        output_dict["y_img"] = output_dict["y_img"] ** 2
        
        # threshhold 
        max_val = np.max(output_dict["y_img"])
        min_val = np.min(output_dict["y_img"])
        threshhold = (max_val - min_val) * 0.5
        # anythin below threshhold is set to min_val
        output_dict["y_img"][output_dict["y_img"] < threshhold] = min_val
        
        # standardise between 0 and 1
        # output_dict["y_img"] = (output_dict["y_img"] - output_dict["y_min"]) / (
        #     output_dict["y_max"] - output_dict["y_min"]
        # )
        # # 255
        # output_dict["y_img"] = output_dict["y_img"] * 255
        
        # ## square anything below 255*0.5
        # output_dict["y_img"][output_dict["y_img"] < 255*0.5] = 255
        
        return output_dict
