import time
from traceback import print_exc

from Motor import *
import RPi.GPIO as GPIO
from commons import Tracking
from servo import Servo


class LineTracker:
    def __init__(self):
        self.IR_LEFT = 14
        self.IR_MID = 15
        self.IR_RIGHT = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR_LEFT, GPIO.IN)
        GPIO.setup(self.IR_MID, GPIO.IN)
        GPIO.setup(self.IR_RIGHT, GPIO.IN)
        self.recent_track = Tracking.FORWARD

    def get_tracking(self) -> Tracking:
        left: bool = bool(GPIO.input(self.IR_LEFT))
        mid: bool = bool(GPIO.input(self.IR_MID))
        right: bool = bool(GPIO.input(self.IR_RIGHT))

        if mid:
            if left and right:
                pass
            elif left:  # Turn hard left
                self.recent_track = Tracking.LEFT2
                # PWM.setMotorModel(-2000, -2000, 4000, 4000)
            elif right:  # Turn hard right
                self.recent_track = Tracking.RIGHT2
                # PWM.setMotorModel(4000, 4000, -2000, -2000)
            else:  # Drive forward
                self.recent_track = Tracking.FORWARD
                # PWM.setMotorModel(800, 800, 800, 800)

        return self.recent_track


if __name__ == '__main__':
    print('Program is starting ... ')
    aligner = LineTracker()
    try:
        while True:
            align = LineTracker.get_tracking()
            PWM.setMotorModel(*(align.value))

    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)