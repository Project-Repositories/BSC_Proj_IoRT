import sys
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

        self.turn_mode = False


    def get_tracking(self) -> Tracking:
        left: bool = bool(GPIO.input(self.IR_LEFT))
        mid: bool = bool(GPIO.input(self.IR_MID))
        right: bool = bool(GPIO.input(self.IR_RIGHT))
        # print(left,mid,right)
        if self.inverse:
            left = not left
            mid = not mid
            right = not right

        if mid:
            if left and right:
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
        elif left and right:  # left and right detected.
            return self.recent_track

        elif left:  # Turn slightly left
            self.recent_track = Tracking.LEFT1
            # PWM.setMotorModel(-1500, -1500, 2500, 2500)
        elif right:  # Turn slightly right
            self.recent_track = Tracking.RIGHT1
            # PWM.setMotorModel(2500, 2500, -1500, -1500)

        return self.recent_track


IR01 = 14
IR02 = 15
IR03 = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR01,GPIO.IN)
GPIO.setup(IR02,GPIO.IN)
GPIO.setup(IR03,GPIO.IN)
class Old_Line_Tracking:
    def run(self):
         while True:
             self.LMR=0x00
             if GPIO.input(IR01)==True:
                 self.LMR=(self.LMR | 4)
             if GPIO.input(IR02)==True:
                 self.LMR=(self.LMR | 2)
             if GPIO.input(IR03)==True:
                 self.LMR=(self.LMR | 1)
             if self.LMR==2:
                 PWM.setMotorModel(800,800,800,800)
             elif self.LMR==4:
                 PWM.setMotorModel(-1500,-1500,2500,2500)
             elif self.LMR==6:
                 PWM.setMotorModel(-2000,-2000,4000,4000)
             elif self.LMR==1:
                 PWM.setMotorModel(2500,2500,-1500,-1500)
             elif self.LMR==3:
                 PWM.setMotorModel(4000,4000,-2000,-2000)
             elif self.LMR==7:
                 pass

if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        if True:
            sysargs = [arg.strip().lower() for arg in sys.argv]
            if "inverse" in sysargs:
                arg_inverse = True
            else:
                arg_inverse = False
            aligner = LineTracker(arg_inverse)
            while True:
                align = aligner.get_tracking()
                # print(align)
                PWM.setMotorModel(*align.value)
            
        else:
            linetrack = Old_Line_Tracking()
            linetrack.run()
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
