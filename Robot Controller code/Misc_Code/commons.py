# https://stackoverflow.com/a/58470178
import time
from enum import Enum
from rpi_ws281x import Color


def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


class DriveInstructions(Enum):
    SLOWER = 0
    SLOW = 1  # 600
    BASE = 2  # 1000
    FAST = 3  # 1500
    FASTER = 4  # 2000
    BEGIN = 5  # 1000
    NONE = -1  # None


speed_state_dict = {DriveInstructions.SLOWER: 0,
                    DriveInstructions.SLOW: 600,
                    DriveInstructions.BASE: 1000,
                    DriveInstructions.FAST: 1500,
                    DriveInstructions.FASTER: 2000,
                    DriveInstructions.BEGIN: 1000,
                    DriveInstructions.NONE: None
                    }

# Acceleration happens every 0.5 seconds
acc_state_dict = {DriveInstructions.SLOWER: -50,
                  DriveInstructions.SLOW: -25,
                  DriveInstructions.BASE: 0,
                  DriveInstructions.FAST: 25,
                  DriveInstructions.FASTER: 50,
                  DriveInstructions.BEGIN: 0,
                  DriveInstructions.NONE: None
                  }


class Head(Enum):
    FORWARDS = 1
    BACKWARDS = -1


class NodeType(Enum):
    Child = 0
    Coordinator = 1


def multiply_pwm_values(values, coeff):
    new_values = [int(value * coeff) for value in values]
    return new_values


m = 1  # 0.5


class Tracking(Enum):
    LEFT1 = multiply_pwm_values((-1500, -1500, 2500, 2500), m)  # (0, 0, 2500, 2500) #
    LEFT2 = multiply_pwm_values((-2000, -2000, 4000, 4000), m)  # (0, 0, 4000, 4000)
    FORWARD = [speed_state_dict[DriveInstructions.FASTER]] * 4
    RIGHT1 = multiply_pwm_values((2500, 2500, -1500, -1500), m)  # (2500, 2500, 0, 0)
    RIGHT2 = multiply_pwm_values((4000, 4000, -2000, -2000), m)  # (4000, 4000, 0, 0)
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


led_off = Color(0, 0, 0)
led_red = Color(125, 0, 0)
led_yellow = Color(50, 50, 0)
led_green = Color(0, 125, 0)
