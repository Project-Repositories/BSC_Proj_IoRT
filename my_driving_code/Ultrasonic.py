import math
import time
from Motor import *
import RPi.GPIO as GPIO
from servo import *
from PCA9685 import PCA9685


class Ultrasonic:
    """
    Some approximate specs for the ultrasonic device can be found here:
    https://howtomechatronics.com/tutorials/arduino/ultrasonic-sensor-hc-sr04/
    """

    def __init__(self):
        GPIO.setwarnings(False)
        self.trigger_pin = 27
        self.echo_pin = 22
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def send_trigger_pulse(self):
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00015)
        GPIO.output(self.trigger_pin, False)

    def wait_for_echo(self, value, timeout):
        start_time = time.time()
        passed_time = 0
        sec_to_microsec = 1000000  # 1.000.000
        while GPIO.input(self.echo_pin) != value and (passed_time < timeout):
            passed_time = (time.time() - start_time) # * sec_to_microsec  # microseconds.

    def get_distance(self, num_measurements: int = 5):
        sound_speed_cm_per_second = 34300
        distance_cm = [0] * num_measurements
        for i in range(num_measurements):
            self.send_trigger_pulse()
            self.wait_for_echo(True, 2) # 10000
            start = time.time()
            self.wait_for_echo(False, 2)
            finish = time.time()
            pulse_len = finish - start
            distance = pulse_len * sound_speed_cm_per_second  # distance = time * speed
            distance /= 2  # divide by 2 since the soundwave travels forth and back before received.
            distance_cm[i] = distance
            
        distance_cm = sorted(distance_cm)
        if num_measurements % 2:  # case of Odd
            # take the median value of the distances
            middle_index = num_measurements // 2
            # print("measured distance : {}".format(int(distance_cm[middle_index])))
            return int(distance_cm[middle_index])
        else:  # case of Even
            # take the average value of the 2 median values.
            medians = (distance_cm[math.floor(num_measurements / 2)],
                       distance_cm[math.ceil(num_measurements / 2)])
            print("measured distance : ".format(round((medians[0] + medians[1]) / 2)))
            return round((medians[0] + medians[1]) / 2)

    def rotate_car(self, direction):
        left_str = "l"
        right_str = "r"
        if direction not in (left_str, right_str):
            raise ValueError("Direction string is invalid")
        if direction == left_str:
            self.PWM.setMotorModel(-1500, -1500, 1500, 1500)
        elif direction == right_str:
            self.PWM.setMotorModel(1500, 1500, -1500, -1500)

    def turn_around_car(self):
        time_to_turn = 2
        self.rotate_car("r")
        time.sleep(time_to_turn)

    def run_motor_1(self, left, mid, right):
        close_distance = 30
        closer_distance = 20
        closest_distance = 10

        if (left < close_distance and mid < close_distance and right < close_distance) or mid < close_distance:
            # Drive backwards
            self.PWM.setMotorModel(-1450, -1450, -1450, -1450)
            time.sleep(0.1)
            if left < right:
                self.rotate_car("r")
            else:
                self.rotate_car("l")
        elif left < close_distance and mid < close_distance:
            PWM.setMotorModel(1500, 1500, -1500, -1500)
        elif right < close_distance and mid < close_distance:
            PWM.setMotorModel(-1500, -1500, 1500, 1500)
        elif left < closer_distance:
            PWM.setMotorModel(2000, 2000, -500, -500)
            if left < closest_distance:
                PWM.setMotorModel(1500, 1500, -1000, -1000)
        elif right < closer_distance:
            PWM.setMotorModel(-500, -500, 2000, 2000)
            if right < closest_distance:
                PWM.setMotorModel(-1500, -1500, 1500, 1500)
        else:
            self.PWM.setMotorModel(600, 600, 600, 600)

    def run_motor_2(self, left, mid, right):
        close_distance = 30
        closer_distance = 20
        closest_distance = 10

        if (left < close_distance and mid < close_distance and right < close_distance) or mid < close_distance:
            # Drive backwards
            self.PWM.setMotorModel(-1450, -1450, -1450, -1450)
            time.sleep(0.1)
            # Turn around
            self.turn_around_car()
        else:
            self.PWM.setMotorModel(600, 600, 600, 600)

    def run(self):
        self.PWM = Motor()
        self.pwm_S = Servo()
        for i in range(30, 151, 60):
            self.pwm_S.setServoPwm('0', i)
            time.sleep(0.2)
            if i == 30:
                L = self.get_distance()
            elif i == 90:
                M = self.get_distance()
            else:
                R = self.get_distance()
        while True:
            for i in range(90, 30, -60):
                self.pwm_S.setServoPwm('0', i)
                time.sleep(0.2)
                if i == 30:
                    L = self.get_distance()
                elif i == 90:
                    M = self.get_distance()
                else:
                    R = self.get_distance()
                self.run_motor_1(L, M, R)
            for i in range(30, 151, 60):
                self.pwm_S.setServoPwm('0', i)
                time.sleep(0.2)
                if i == 30:
                    L = self.get_distance()
                elif i == 90:
                    M = self.get_distance()
                else:
                    R = self.get_distance()
                # self.run_motor_1(L, M, R)
                self.run_motor_2(L, M, R)


ultrasonic = Ultrasonic()
# Main program logic follows:
if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        ultrasonic.run()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
        ultrasonic.pwm_S.setServoPwm('0', 90)
