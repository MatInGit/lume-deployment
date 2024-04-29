from lume_model.base import LUMEBaseModel

import numpy as np

class ExampleModel(LUMEBaseModel):
    def evaluate(self, input_dict):
        output_dict = {}
        output_dict["y"] = np.max([input_dict["x1"], input_dict["x2"]])
        return output_dict

class ExampleImageModel():

    def evaluate(self,input_dict):
        output_dict = {}
        
        # input will contain an image (np.array), we want to return the image
        output_dict["y_max"] = np.max(input_dict["image"])
        output_dict["y_min"] = np.min(input_dict["image"])
        output_dict["y_mean"] = np.mean(input_dict["image"])
        output_dict["y_std"] = np.std(input_dict["image"])

            
        # output_dict["y_img"] = np.rot90(input_dict["image"], k=1, axes=(0, 1))
        
        # gaussian filter
        output_dict["y_img"] = input_dict["image"]**2
        
        
        
        return output_dict