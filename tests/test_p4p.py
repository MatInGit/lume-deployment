from mm.interfaces import SimplePVAInterface
from mm.logging_utils.make_logger import get_logger, make_logger
import numpy as np
import subprocess
import pytest


# start mailbox.py as a subprocess

logger = make_logger("model_manager")

process = None

# run before tests 
@pytest.fixture(scope="session", autouse=True)
def setup():
    global process
    # process = subprocess.Popen(["python", "mailbox.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process = subprocess.Popen(["python", "./tests/mailbox.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    yield
    process.kill()
    

def test_SimplePVAInterface_init():
    

    config = {
        "variables": {
            "test:float:AA": {
                "name": "test:float:AA",
                "proto": "pva"},
            "test:float:BB": {
                "name": "test:float:BB",
                "proto": "pva"
            }
        }
    }
    logger.info("Testing SimplePVAInterface init")
    p4p = SimplePVAInterface(config)
    nameA, valA = p4p.get("test:float:AA")
    assert valA["value"] == 0
    
    p4p.put("test:float:AA", 1)
    p4p.put("test:float:BB", 2)
    nameA, valA = p4p.get("test:float:AA")
    nameB, valB = p4p.get("test:float:BB")
    print(nameA, nameB, valA, valB)
    assert valA["value"] == 1
    assert valB["value"] == 2
    assert nameA == "test:float:AA"
    assert nameB == "test:float:BB"
    p4p.close()

def test_SimplePVAInterface_put_and_get_image():

    config = {
        "variables": {
            "test:image:AA": {
                "name": "test:image:AA",
                "proto": "pva",
                "type": "image",
            }
        }
    }
    p4p = SimplePVAInterface(config)
    
    name, image_get = p4p.get("test:image:AA")
    shape = image_get["value"].shape
    print(shape)
    assert image_get["value"][0][0] == 1 # should be intialized to 1 by mailbox.py
    
    arry = np.random.rand(shape[0], shape[1])
    p4p.put("test:image:AA", arry)
    name, image_get = p4p.get("test:image:AA")
    print(type(image_get["value"]))
    assert image_get["value"][0][0] == arry[0][0]
    
    p4p.close()


