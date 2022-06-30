import sys
import time
from traceback import print_exc

from Hardware_Controllers.Motor import *
import RPi.GPIO as GPIO
from Misc_Code.commons import Tracking
from Hardware_Controllers.servo import Servo

class LineTracker:
    def __init__(self, inverse_light: bool, turn_mode_enabled: bool = False):
        # 'inverse' denotes if the IR signal should be negated.
        # Standard configuration is IR sensors sending a HIGH signal when detecting a black tape line.
        # If the ground surface is dark, and the line is bright, then inverse_light should be True.
        self.inverse = inverse_light

        # 'Turn mode' is activated/deactivated when all IR sensors detect a line of tape,
        # i.e. a line of tape orthogonal to the current direction.
        # Turn mode means the car drives slower,
        # and is used to avoid the car driving off-course during curved portions of the route
        self.turn_mode_enabled = turn_mode_enabled

        # Defining the infrared sensor pins
        self.IR_LEFT = 14
        self.IR_MID = 15
        self.IR_RIGHT = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR_LEFT, GPIO.IN)
        GPIO.setup(self.IR_MID, GPIO.IN)
        GPIO.setup(self.IR_RIGHT, GPIO.IN)

        # Default values
        self.recent_track = Tracking.FORWARD
        self.turn_mode = False

    def _get_tracking(self) -> Tracking:
        """
        Function which contains the line-tracking logic.
        Consider testing if swapping the sharp and soft turns results in better line-tracking.
        """
        left: bool = bool(GPIO.input(self.IR_LEFT))
        mid: bool = bool(GPIO.input(self.IR_MID))
        right: bool = bool(GPIO.input(self.IR_RIGHT))

        if self.inverse:
            left = not left
            mid = not mid
            right = not right

        if mid:
            if left and right:  # Switch turn_mode status
                if self.turn_mode_enabled:
                    self.turn_mode = not self.turn_mode
                time.sleep(0.05)
            elif left:  # Turn hard left
                self.recent_track = Tracking.LEFT2
            elif right:  # Turn hard right
                self.recent_track = Tracking.RIGHT2
            else:  # Drive forward
                if self.turn_mode:
                    self.recent_track = Tracking.SLOW
                else:
                    self.recent_track = Tracking.FORWARD
        elif left and right:  # Continue with most recent track action
            return self.recent_track
        elif left:  # Turn slightly left
            self.recent_track = Tracking.LEFT1
        elif right:  # Turn slightly right
            self.recent_track = Tracking.RIGHT1
        return self.recent_track

    def get_alignment(self) -> tuple[int]:
        return self._get_tracking().value


if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        sys_args = [arg.strip().lower() for arg in sys.argv]
        if "inverse" in sys_args:
            arg_inverse = True
        else:
            arg_inverse = False
        aligner = LineTracker(arg_inverse)
        while True:
            align = aligner.get_alignment()
            PWM.setMotorPWM(align)
            PWM.setMotorModel(align)
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
