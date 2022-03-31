import time
from Motor import *
import RPi.GPIO as GPIO


class Line_Tracking:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

    def run(self):
        can_inverse = False
        direction = 1

        # Old values:
        # 1: (2500, 2500, -1500, -1500) turn sharp
        # (800, 800, -400, -400)
        # 3: (4000, 4000, -2000, -2000) turn soft left
        # (1000, 1000, -500, -500)
        # 4: (-1500, -1500, 2500, 2500) turn sharp right
        # (-400, -400, 800, 800)
        # 6: (-2000, -2000, 4000, 4000) turn soft left
        # (-500, -500, 1000, 1000)
        # TODO: Sharper turns, check sensors more frequently.
        # Too low values results in poor turning/driving.
        action_dict = {1: (2500, 2500, -1500, -1500), 2: (600, 600, 600, 600),
                       3: (4000, 4000, -2000, -2000), 4: (-1500, -1500, 2500, 2500),
                       6: (-2000, -2000, 4000, 4000)}

        while True:
            le_mi_ri = 0  # accumulating value for the three infrared sensors.
            if GPIO.input(self.IR01):  # Left
                le_mi_ri += 4
            if GPIO.input(self.IR02):  # Middle
                le_mi_ri += 2
            if GPIO.input(self.IR03):  # Right
                le_mi_ri += 1
            motor_values = action_dict.get(le_mi_ri, (600, 600, 600, 600))  # default value is to slowly drive straight.
            # motor_values = (600, 600, 600, 600)
            if le_mi_ri in (0, 2):
                if le_mi_ri == 0 and can_inverse:
                    direction *= -1  # invert direction
                    can_inverse = False
                elif le_mi_ri == 2:  # if driving straight
                    # can now invert direction, the next time line is not detected.
                    can_inverse = True
                motor_values = [direction * num for num in motor_values]
            elif False and direction == -1 and \
                    le_mi_ri in (1, 3, 4, 6):  # if turning and driving backwards
                pass  # Switch PWM of wheels of left-side with right-side
            motor_values = motor_values[2:4] + motor_values[0:2]
            PWM.setMotorModel(*motor_values)
            time.sleep(0.05 + (0.1 * (direction == -1)))  # time to drive before checking again
            # + (0.1 * can_inverse)

    def run2(self):
        while True:
            le_mi_ri = 0  # accumulating value for the three infrared sensors.
            if GPIO.input(self.IR01):  # Left
                le_mi_ri += 4
            if GPIO.input(self.IR02):  # Middle
                le_mi_ri += 2
            if GPIO.input(self.IR03):  # Right
                le_mi_ri += 1
            if le_mi_ri == 2:
                PWM.setMotorModel(-800, -800, -800, -800)
            elif le_mi_ri == 4:
                PWM.setMotorModel(-1500, -1500, 2500, 2500)
            elif le_mi_ri == 6:
                PWM.setMotorModel(-2000, -2000, 4000, 4000)
            elif le_mi_ri == 1:
                PWM.setMotorModel(2500, 2500, -1500, -1500)
            elif le_mi_ri == 3:
                PWM.setMotorModel(4000, 4000, -2000, -2000)
            elif le_mi_ri == 7:
                # pass
                PWM.setMotorModel(0, 0, 0, 0)


infrared = Line_Tracking()
# Main program logic follows:
if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        infrared.run2()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
