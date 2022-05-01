import time
from enum import Enum
from servo import Servo
from Ultrasonic import ultrasonic
from simple_pid import PID
from Motor import PWM
import RPi.GPIO as GPIO


class Direction(Enum):
    LEFT = 0
    RIGHT = 180


class WallAligner:
    """
    PID explained:
    Ultrasonic sensor chosen to point in either right of left direction.
    Initial distance is measured.
    Then, change in distance to wall in chosen direction is measured.
    By modifying the speed of 2 wheels on the chosen side, we can turn the car
    until the distance is returned to initial condition.
    To turn the car the correct direction,
    an increase in distance should lead to decrease in RPM of chosen wheels.
    This means the PID coefficients should be negative.
    """

    def __init__(self, direction: Direction):
        self.direction = direction
        self.ultrasonic = ultrasonic()
        self.pwm_Servo = Servo()
        self.pwm_Servo.setServoPwm(self.direction.value)
        time.sleep(0.1)  # Wait until servo has moved
        # Measure the initial distance to wall:
        self.target_distance = self.ultrasonic.get_distance()

        # Needs to be evaluated experimentally:
        self.pid = PID(-1, -0.1, -0.05, setpoint=0)
        self.pid.output_limits = (-50, 50)

    def get_direction_correction(self, speed_magnitude: int):
        # calculate error by measuring difference of current distance to target distance:
        distance_error = self.ultrasonic.get_distance() - self.target_distance
        control_value = self.pid(distance_error)
        controlled_wheel_magnitude = (100 + control_value) * speed_magnitude
        return controlled_wheel_magnitude


class SimpleDriver:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

    def oscillate_simple(self):
        fwd_motor_values = [1000, 1000, 1000, 1000]  # configured to calibrate for the robot's left-leaning tendency

        def drive(direction):
            motor_values = [direction * num for num in fwd_motor_values]
            PWM.setMotorModel(*motor_values)

        direction = 1

        turn_time = 2.5
        previous_turn = time.time()
        while True:
            current_time = time.time()
            if current_time - previous_turn >= turn_time:
                previous_turn = current_time
                direction *= -1
            drive(direction)


def test_pid():
    tst_value = 10
    target_value = 0
    pid = PID(1, 0, 0.0, setpoint=target_value)
    for i in range(100):
        control = pid(tst_value)
        tst_value = tst_value + control
        if i % 10 == 0:
            print(f"{control = }")
            print(f"{tst_value = }")

if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        driver = SimpleDriver()
        driver.oscillate_simple()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
