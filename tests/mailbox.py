# mail box server for testing
from p4p.server import Server
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV
from p4p.nt import NTScalar, NTNDArray
import numpy as np

# get all upper case alphabet
import string

ALPHABET = string.ascii_uppercase

name_proto_float = "test:float:"
name_proto_image = "test:image:"


pv_list = [name_proto_float + letter + letter for letter in ALPHABET]
pv_list_image = [name_proto_image + letter + letter for letter in ALPHABET]

shared_pvs = []

for pv in pv_list:
    # self.shared_pvs.append(pv)
    pv_item = {}
    pv_item[pv] = SharedPV(nt=NTScalar("d"), initial=0)

    @pv_item[pv].put
    def put(pv: SharedPV, op: ServOpWrap):
        pv.post(op.value())
        op.done()

    shared_pvs.append(pv_item)

for pv in pv_list_image:
    x_size = np.random.randint(10, 200)
    y_size = 10
    # intialize with zeros
    intial_value = np.ones((x_size, y_size))
    pv_type_nt = NTNDArray()
    pv_type_init = intial_value

    pv_item = {}
    pv_item[pv] = SharedPV(nt=pv_type_nt, initial=pv_type_init)

    @pv_item[pv].put
    def put(pv: SharedPV, op: ServOpWrap):
        pv.post(op.value())
        op.done()

    shared_pvs.append(pv_item)

print(shared_pvs)
Server.forever(providers=shared_pvs)
