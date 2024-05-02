import numpy as np
import matplotlib.pyplot as plt

# visualize = True

# if visualize:
#     plt.ion()
#     figure = plt.figure()
#     axes = figure.add_subplot(111)
#     axes.set_title("Example Image Model")

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
        
        # if visualize:
        #     figure.clear()
        #     axes = figure.add_subplot(111)
        #     axes.set_title("Example Image Model")
        #     axes.imshow(output_dict["y_img"], origin="lower")
        #     # print(input_dict["image"].shape)
        #     plt.draw()
        #     plt.pause(0.0001)
        

        return output_dict


class ModelFactory: # used to create model instances when in local mode
    @staticmethod
    def get_model():
        return ExampleImageModel()