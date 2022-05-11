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

class Tracking(Enum):
    LEFT1 = (-1500, -1500, 2500, 2500)
    LEFT2 = (-2000, -2000, 4000, 4000)
    FORWARD = (800, 800, 800, 800)
    RIGHT1 = (2500, 2500, -1500, -1500)
    RIGHT2 = (4000, 4000, -2000, -2000)



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
