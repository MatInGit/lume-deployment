from abc import ABC, abstractmethod

class BaseTransformer:
    @abstractmethod
    def __init__(self, config):
        """
        config: dict passed from the pv_mappings.yaml files
        """
        pass
    
    @abstractmethod
    def transform(self):
        """
        Initiate transform function to transform the input data
        """
        pass
    
    @abstractmethod
    def handler(self, pv_name, value):
        """
        Handler function to handle the input data, in most cases it initiates the transform function when all the input data is available. 
        Handler is the only function exposed to the main loop of the program aside from initial configuration.
        """
        pass
    

