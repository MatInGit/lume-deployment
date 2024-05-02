from p4p.client.thread import Context
# server
from p4p.server import Server
from p4p.nt import NTScalar, NTNDArray
from p4p.server.thread import SharedPV
import numpy as np
ctxt = Context("pva")
from matplotlib import pyplot as plt

arry = ctxt.get("LUME:MLFLOW:TEST_IMAGE")


fig, ax = plt.subplots()
plt.ion()

while True:
    arry = ctxt.get("LUME:MLFLOW:TEST_IMAGE")
    ax.clear()
    ax.imshow(arry.data, origin="lower")
    plt.pause(0.1)
    