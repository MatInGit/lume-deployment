# mail box server for testing
from p4p.server import Server
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV
from p4p.nt import NTScalar, NTTable

# get all upper case alphabet
import string

ALPHABET = string.ascii_uppercase

name_proto_float = "LUME:MLFLOW:TEST_MAILBOX:D:"
# name_proto_image = "LUME:MLFLOW:TEST_MAILBOX:I:"


pv_list = [name_proto_float + letter + letter for letter in ALPHABET]

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


Server.forever(providers=shared_pvs)
