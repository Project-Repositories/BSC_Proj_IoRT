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
        direction = 1
        action_dict = {1: (2500, 2500, -1500, -1500), 2: (800, 800, 800, 800),
                       3: (4000, 4000, -2000, -2000), 4: (-1500, -1500, 2500, 2500),
                       6: (-2000, -2000, 4000, 4000)}

        while True:
            le_mi_ri = 0  # left middle right
            if GPIO.input(self.IR01):
                le_mi_ri += 4
            if GPIO.input(self.IR02):
                le_mi_ri += 2
            if GPIO.input(self.IR03):
                le_mi_ri += 1
            motor_values = action_dict.get(self.LMR, default=(600, 600, 600, 600))
            if action_dict in (0, 5, 7):
                direction *= -1  # invert direction
            motor_values = [direction * num for num in motor_values]
            PWM.setMotorModel(*motor_values)


infrared = Line_Tracking()
# Main program logic follows:
if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        infrared.run()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
