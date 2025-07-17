import logging
import time

import torch
from torch import nn

# simple PID controller implemented using pytorch, it has calculates the error and tracks the history
# if the error is greater than the threshold, enable the adaptive learning on each step
# the adaptive learning uses backpropagation to update the parameters of the PID controller

logger = logging.getLogger("model_manager")


class PID(nn.Module):
    def __init__(self, P=0.1, I=0.01, D=0.01, threshold=0.1, dt=0.1, lr=0.01):
        super().__init__()
        self.P = nn.Parameter(torch.tensor(P), requires_grad=True)
        self.I = nn.Parameter(torch.tensor(I), requires_grad=True)
        self.D = nn.Parameter(torch.tensor(D), requires_grad=True)
        self.threshold = threshold
        self.error = 0
        self.integral = 0
        self.prev_error = 0
        self.set_point_history = torch.tensor([], requires_grad=True)
        self.input_history = torch.tensor([], requires_grad=True)
        self.output_history = torch.tensor([], requires_grad=True)
        self.error_history = torch.tensor([], requires_grad=True)
        self.dt = dt
        self.adaptive = False
        self.lr = lr
        self.loss = nn.MSELoss()
        self.last_update = time.time()
        self.last_output = 0

    def forward(self, setpoint, system_output):
        logger.info(f"Setpoint: {setpoint}, System Output: {system_output}")
        if time.time() - self.last_update > 1:
            self.last_update = time.time()
            if self.adaptive:
                self.adapt()
            logger.info(
                f"Setpoint: {setpoint}, System Output: {system_output}, Error: {self.error}"
            )
            self.error = setpoint - system_output
            self.integral += self.error * self.dt
            derivative = (self.error - self.prev_error) / self.dt
            self.prev_error = self.error
            output = self.P * self.error + self.I * self.integral + self.D * derivative
            self.input_history = torch.cat(
                (self.input_history, torch.tensor([system_output]))
            )
            self.set_point_history = torch.cat(
                (self.set_point_history, torch.tensor([setpoint]))
            )
            self.output_history = torch.cat(
                (self.output_history, torch.tensor([output]))
            )
            self.error_history = torch.cat(
                (self.error_history, torch.tensor([self.error]))
            )
            self.last_output = output
        else:
            output = self.last_output

        # if last 10 errors are less than threshold, adapt false
        if len(self.error_history) > 5:
            if (
                all([abs(e) > self.threshold for e in self.error_history[-5:]])
                and not self.adaptive
            ):
                self.adaptive = True
                logger.info("Adaptive learning enabled")
            if (
                all([abs(e) <= self.threshold for e in self.error_history[-5:]])
                and self.adaptive
            ):
                self.adaptive = False
                logger.info("Adaptive learning disabled")

        return output

    def adapt(self):
        self.zero_grad()
        loss = self.loss(self.output_history[-1], self.set_point_history[-1])
        loss.backward()
        print(f"Loss: {loss}")
        with torch.no_grad():
            for param in self.parameters():
                if param.grad is not None:  # Check if the gradient is not None
                    param -= self.lr * param.grad
        logger.info(f"Adapted PID: P: {self.P}, I: {self.I}, D: {self.D}")
        # self.input_history = torch.tensor([], requires_grad=True)
        # self.output_history = torch.tensor([], requires_grad=True)
        # self.error_history = torch.tensor([], requires_grad=True)
        # self.set_point_history = torch.tensor([], requires_grad=True)

    def reset(self):
        self.error = 0
        self.integral = 0
        self.prev_error = 0
        self.input_history = []
        self.output_history = []
        self.error_history = []
        self.adaptive = False
        self.zero_grad()

    def evaluate(self, input_dict):
        return {
            "new_input": self.forward(
                input_dict["setpoint"], input_dict["system_output"]
            )
        }


class ModelFactory:  # used to create model instances when in local mode
    @staticmethod
    def get_model():
        return PID()
