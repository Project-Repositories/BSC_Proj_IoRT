import time
from traceback import print_exc

from Motor import *
import RPi.GPIO as GPIO
from commons import Tracking
from servo import Servo


class LineTracker:
    def __init__(self, inverse_light: bool):
        self.IR_LEFT = 14
        self.IR_MID = 15
        self.IR_RIGHT = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR_LEFT, GPIO.IN)
        GPIO.setup(self.IR_MID, GPIO.IN)
        GPIO.setup(self.IR_RIGHT, GPIO.IN)
        self.recent_track = Tracking.FORWARD
        self.inverse = inverse_light

    def get_tracking(self) -> Tracking:
        left: bool = bool(GPIO.input(self.IR_LEFT))
        mid: bool = bool(GPIO.input(self.IR_MID))
        right: bool = bool(GPIO.input(self.IR_RIGHT))

        if self.inverse:
            left = not left
            mid = not mid
            right = not right

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
        if (left and right) or not (left and mid and right):  # If no line detected, or left and right detected,
            # use the most recent instruction instead.
            pass
        elif left:  # Turn slightly left
            self.recent_track = Tracking.LEFT1
            PWM.setMotorModel(-1500, -1500, 2500, 2500)
        elif right:  # Turn slightly right
            self.recent_track = Tracking.RIGHT1
            # PWM.setMotorModel(2500, 2500, -1500, -1500)

        return self.recent_track


if __name__ == '__main__':
    print('Program is starting ... ')
    aligner = LineTracker(True)
    try:
        while True:
            align = aligner.get_tracking()
            PWM.setMotorModel(*align.value)

    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
