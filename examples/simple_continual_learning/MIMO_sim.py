import time

import matplotlib.pyplot as plt
import numpy as np
from p4p.nt import NTScalar
from p4p.server import Server
from p4p.server.raw import ServOpWrap
from p4p.server.thread import SharedPV


class RandomMIMO_System:
    def __init__(self, n, m, p, dt=0.01):
        self.n = n  # state dimension
        self.m = m  # input dimension
        self.p = p  # output dimension

        self.A = -np.eye(n) + np.random.randn(n, n) * 0.7  # generally stable systems
        self.B = np.random.randn(n, m)
        self.C = np.random.randn(p, n)
        self.dt = dt

    def step(self, x, u):
        x = (
            self.A @ x * self.dt
            + self.B @ u * self.dt
            + x
            + np.random.randn(self.n) * 0.001
        )  # little bit of noise to make it interesting
        return x

    def output(self, x):
        y = self.C @ x
        return y

    def reset(self):
        return np.random.randn(self.n)

    def plot_phase_portraits(self):
        # for each pair of states, plot the phase portrait but only off-diagonal

        # n_plots = triangular number of n for n>2 else 1 for n=2 and 0 for n=1
        unique_states = []
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                new_set = {i, j}
                if new_set not in unique_states:
                    unique_states.append(new_set)

        print(unique_states)

        fig, axs = plt.subplots(len(unique_states), 1)

        for z, test_set in enumerate(unique_states):
            # find phase portrait for states i and j
            X = np.linspace(-10, 10, 10)
            Y = np.linspace(-10, 10, 10)
            X, Y = np.meshgrid(X, Y)
            set_to_list = list(test_set)
            i = set_to_list[0]
            j = set_to_list[1]
            U = self.A[i, i] * X + self.A[i, j] * Y
            V = self.A[j, i] * X + self.A[j, j] * Y
            if len(unique_states) == 1:
                axs.streamplot(X, Y, U, V)
                axs.set_xlabel('State ' + str(i))
                axs.set_ylabel('State ' + str(j))
            else:
                axs[z].streamplot(X, Y, U, V)
                axs[z].set_xlabel('State ' + str(i))
                axs[z].set_ylabel('State ' + str(j))

        plt.show()


states = 2
inputs = 1
outputs = 1
dt = 0.05

mimo = RandomMIMO_System(2, 1, 1, dt=dt)
mimo.plot_phase_portraits()


x = mimo.reset()

name_proto_float = 'lume:test:mimo:test:'


pv_list_state = [name_proto_float + 'state_' + str(i) for i in range(states)]
pv_list_input = [name_proto_float + 'input_' + str(i) for i in range(inputs)]
pv_list_output = [name_proto_float + 'output_' + str(i) for i in range(outputs)]

pv_list = pv_list_state + pv_list_input + pv_list_output

shared_pvs = []
shared_pv_lookup = {}
for pv in pv_list:
    # self.shared_pvs.append(pv)
    pv_item = {}
    pv_item[pv] = SharedPV(nt=NTScalar('d'), initial=0)

    @pv_item[pv].put
    def put(pv: SharedPV, op: ServOpWrap):
        pv.post(op.value())
        op.done()

    shared_pvs.append(pv_item)
    shared_pv_lookup[pv] = pv_item[pv]

print(shared_pvs)


with Server(providers=shared_pvs) as S:
    last_update = time.time()
    while True:
        inputs_latest = []
        if time.time() - last_update > dt:
            for i in range(inputs):
                inputs_latest.append(shared_pv_lookup[pv_list_input[i]].current())

            x = mimo.step(x, inputs_latest)
            y = mimo.output(x)
            for output in y:
                shared_pv_lookup[pv_list_output[0]].post(output, timestamp=time.time())

            last_update = time.time()
