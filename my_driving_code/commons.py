# https://stackoverflow.com/a/58470178
import time
from enum import Enum


def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


class DriveInstructions(Enum):
    SLOWER = 0
    SLOW = 600
    BASE = 1000
    FAST = 1500
    FASTER = 2000
    BEGIN = 1000
    NONE = None


class Head(Enum):
    FORWARDS = 1
    BACKWARDS = -1


class NodeType(Enum):
    Child = 0
    Coordinator = 1


def multiply_pwm_values(values, coeff):
    new_values = [int(value * coeff) for value in values]
    return new_values


m = 1 #  0.5


class Tracking(Enum):
    LEFT1 = multiply_pwm_values((-1500, -1500, 2500, 2500), m)
    LEFT2 = multiply_pwm_values((-2000, -2000, 4000, 4000), m)
    FORWARD = [DriveInstructions.BASE] * 4
    RIGHT1 = multiply_pwm_values((2500, 2500, -1500, -1500), m)
    RIGHT2 = multiply_pwm_values((4000, 4000, -2000, -2000), m)
    SLOW = (800, 800, 800, 800)  # Turn mode, activated around the ends of the line


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
