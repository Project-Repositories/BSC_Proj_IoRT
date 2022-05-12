# https://stackoverflow.com/a/58470178
import time
from enum import Enum


def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


class Head(Enum):
    FORWARDS = 1
    BACKWARDS = -1


class NodeType(Enum):
    Child = 0
    Coordinator = 1

def multiply_pwm_values(values, coeff):
    new_values = [int(value * coeff) for value in values]
    return new_values

m = 0.85

class Tracking(Enum):
    LEFT1 = multiply_pwm_values((-1500, -1500, 2500, 2500),m)
    LEFT2 = multiply_pwm_values((-2000, -2000, 4000, 4000), m)
    FORWARD = multiply_pwm_values((4000, 4000, 4000, 4000),1/5) # (2000, 2000, 2000, 2000)
    RIGHT1 = multiply_pwm_values((2500, 2500, -1500, -1500), m)
    RIGHT2 = multiply_pwm_values((4000, 4000, -2000, -2000), m)


class Timer:
    def __init__(self, period):
        self.period = period
        self.previous_timestamp = time.time()

    def check(self):
        current_time = time.time()
        if current_time - self.previous_timestamp >= self.period:
            self.previous_timestamp = current_time
            return True
        else:
            return False
