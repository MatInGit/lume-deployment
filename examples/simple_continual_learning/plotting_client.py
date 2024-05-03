from p4p.client.thread import Context
# server
from p4p.server import Server
from p4p.nt import NTScalar, NTNDArray
from p4p.server.thread import SharedPV
import numpy as np
ctxt = Context("pva")
from matplotlib import pyplot as plt


fig, ax = plt.subplots()
plt.ion()

input = []
output = []
state0 = []
state1 = []

# [{'lume:test:mimo:test:state_0': SharedPV(value=0.0)}, {'lume:test:mimo:test:state_1': SharedPV(value=0.0)}, {'lume:test:mimo:test:input_0': SharedPV(value=0.0)}, {'lume:test:mimo:test:output_0': SharedPV(value=0.0)}]



while True:
    input.append(ctxt.get("lume:test:mimo:test:input_0"))
    output.append(ctxt.get("lume:test:mimo:test:output_0"))
    state0.append(ctxt.get("lume:test:mimo:test:state_0"))
    state1.append(ctxt.get("lume:test:mimo:test:state_1"))
    if len(input) > 100:
        input.pop(0)
        output.pop(0)
        state0.pop(0)
        state1.pop(0)
    ax.clear()
    ax.plot(input, label="Input")
    ax.plot(output, label="Output")
    ax.plot(state0, label="State 0")
    ax.plot(state1, label="State 1")
    ax.legend()
    plt.pause(0.1)
    