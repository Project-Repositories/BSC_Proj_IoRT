import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import Head, NodeType, Timer, Tracking, DriveInstructions
from Hardware_Controllers.parse_UART import UART_Comm


class LineDriver:
    def __init__(self, inverse_IR: bool):
        self.inverse_IR = inverse_IR
        self.tracker = LineTracker(inverse_IR)

    def line_driving(self):
        debug_i = 0
        while True:
            debug_i += 1
            # ------ alignment ------
            alignment = self.tracker.get_alignment()
            PWM.setMotorPWM(alignment)


if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        sysargs = [arg.strip().lower() for arg in sys.argv]
        if "inverse" in sysargs:
            arg_inverse = True
        else:
            arg_inverse = False

        print(("." * 10 + "\nStarting driver. IR inverse: {}\n" + "." * 10).
              format(arg_inverse))
        driver = LineDriver(arg_inverse)
        driver.line_driving()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)