from mm.interfaces import SimlePVAInterfaceServer
from mm.logging_utils.make_logger import get_logger, make_logger
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
    
    