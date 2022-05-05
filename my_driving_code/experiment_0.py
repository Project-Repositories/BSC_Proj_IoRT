import math
import time
import RPi.GPIO as GPIO
from Motor import PWM
from servo import Servo

from enum import Enum
from commons import clamp
from wall_alignment import WallAligner, Direction
from simple_pid import PID


class Head(Enum):
    FORWARDS = 1
    BACKWARDS = -1
# TODO: Move to separate python script ("experiment_1")
# Then, add support for Command Line Arguments, such as base speed & direction.


class SimpleDriver:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

        self.direction = Direction.LEFT
        self.aligner = WallAligner(self.direction)
        self.head = Head.FORWARDS

    def reverse_head(self):
        if self.head == Head.FORWARDS:
            self.head = Head.BACKWARDS
        elif self.head == Head.BACKWARDS:
            self.head = Head.FORWARDS
        else:
            raise ValueError("self.HEAD is of incorrect value and/or type.")

    def oscillate_simple(self):
        def drive(pwm_magnitudes):
            motor_values = [self.head.value * int(num) for num in pwm_magnitudes]
            PWM.setMotorModel(*motor_values)

        def reversal(pwm_magnitude):
            print("reversing")
            speed_sign = self.head.value
            new_speed = pwm_magnitude
            step_size = 500
            n_steps = abs(pwm_magnitude) // step_size

            # Reduce speed linearly:
            for step in range(n_steps + 1):
                if speed_sign is 1:
                    new_speed = max(new_speed - step_size, 0)
                else:
                    new_speed = min(new_speed + step_size, 0)
                PWM.setMotorModel(*[new_speed] * 4)
                time.sleep(0.2)
            self.reverse_head()

        turn_time = 2
        previous_turn = time.time()

        base_speed = 1000
        # to scale alignment accordingly to the speed the PID was tested with (1000):
        align_coeff = (base_speed / 1000) ** 0.5
        fwd_motor_values = [base_speed] * 4

        i = 0
        while True:
            i += 1
            # fwd_motor_values = [base_speed] * 4
            current_time = time.time()
            if current_time - previous_turn >= turn_time:
                previous_turn = current_time
                reversal(base_speed)
            if i % 5 == 0:
                
                align_value = self.aligner.get_direction_correction(base_speed)
                align_value *= align_coeff
                # Clamp the alignment, to limit it from stopping a set of wheels completely, or even reversing the direction.
                align_value = clamp(align_value, -base_speed // 1, base_speed // 1)
                # Split the "burden" of alignment in two parts:
                # One side drives faster, another drives slower, compared to base_speed.
                # Will result in less sudden changes of PWM in a set of wheels, and also be closer to "base speed"
                align_half = align_value / 2
                if self.direction == Direction.RIGHT:
                    # align_half * 1.5
                    fwd_motor_values = [base_speed + align_half] * 2 + \
                                       [base_speed - align_half] * 2
                elif self.direction == Direction.LEFT:
                    fwd_motor_values = [base_speed - align_half] * 2 + \
                                       [base_speed + align_half] * 2
            if i % 30 == 0:
                print("----")
                print("head:{}".format(self.head))
                print("align_value:{}".format(align_value))
                print("fwd_motor_values:{}".format(fwd_motor_values))
                print("p, i, d: {}, {}, {}".format(*self.aligner.pid.components))
            drive(fwd_motor_values)


def test_pid():
    tst_value = 10
    target_value = 0
    pid = PID(1, 0, 0.0, setpoint=target_value)

    def err_map_test(inp):
        if inp > 0:
            inp *= 1000
        else:
            inp *= -250
        return inp

    pid.error_map = err_map_test

    for i in range(5):
        if i % 2:
            i *= -1
        control = pid(i)
        tst_value = tst_value + control
        if i % 1 == 0:
            print("control = {}".format(control))
            print("tst_value = {}".format(tst_value))


if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        driver = SimpleDriver()
        driver.oscillate_simple()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
