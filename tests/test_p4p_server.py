from src.interfaces import SimlePVAInterfaceServer
from src.transformers import PassThroughTransformer, CompoundTransformer
from src.logging_utils.make_logger import get_logger, make_logger
import numpy as np

logger = make_logger("model_manager")

def test_SimplePVAInterfaceServer_init():
    config = {
        "variables": {
            "test": {
                "name": "test",
                "proto": "pva"
            }
        }
    }
    logger.info("Testing SimplePVAInterfaceServer init")
    p4p = SimlePVAInterfaceServer(config)
    p4p.close()
    
def test_SimplePVAInterfaceServer_put_and_get():
    config = {
        "variables": {
            "test": {
                "name": "test",
                "proto": "pva"
            }
        }
    }
    logger.info("Testing SimplePVAInterfaceServer put")
    p4p = SimlePVAInterfaceServer(config)
    p4p.put("test", 1)
    name, value_dict = p4p.get("test")
    print(name, value_dict)
    assert value_dict["value"] == 1
    assert name == "test"
    p4p.close()
    
def test_SimplePVAInterfaceServer_put_and_get_image():
    config = {
        "variables": {
            "test": {
                "name": "test",
                "proto": "pva",
                "type": "image",
                "image_size": {"x": 10, "y": 10}
            }
        }
    }
    p4p = SimlePVAInterfaceServer(config)
    
    arry = np.ones((10, 10))
    
    p4p.put("test", arry)
    name, value_dict = p4p.get("test")
    print(name, value_dict)
    print(value_dict["value"], type(value_dict["value"]))
    assert value_dict["value"][0][0] == arry[0][0]
    assert value_dict["value"].shape == arry.shape
    assert name == "test"
    p4p.close()
    


# more of an integration test than a unit test
def test_p4p_as_image_input():
    config = {
        "variables": {
            "test": {
                "name": "test",
                "proto": "pva",
                "type": "image",
                "image_size": {"x": 10, "y": 10}
            }
        }
    }
    config_pt = {
    "variables": {
        "IMG1": "test",
        }
    }
    config_compound = {
        "transformers": {
            "transformer_1": {"type": "PassThroughTransformer", "config": config_pt},
        }
    }
        
    
    p4p = SimlePVAInterfaceServer(config)
    pt = CompoundTransformer(config_compound)
    
    p4p.put("test", np.ones((10, 10)))
    name, value_dict = p4p.get("test")
    pt.handler("test", value_dict)
    assert pt.updated == True
    assert pt.latest_transformed["IMG1"].shape == (10, 10)
