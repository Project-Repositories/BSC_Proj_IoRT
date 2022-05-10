import time
import RPi.GPIO as GPIO
from Motor import PWM
from servo import Servo

from traceback import \
    print_exc  # For debugging, to print the entire exception when errors occur, but also handle it gracefully

from commons import clamp, Head
from wall_alignment import WallAligner, Direction


class LineReversalDriver:
    """
    Aligns itself to a wall to it's right or left, depending on direction parameter.
    Drives forward for some time, then reverses when IR sensors detects black color.

    """

    def __init__(self, direction: Direction):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

        self.direction = direction  # Direction.LEFT
        self.aligner = WallAligner(self.direction)
        self.head = Head.FORWARDS

    def reverse_head(self):
        if self.head == Head.FORWARDS:
            self.head = Head.BACKWARDS
        elif self.head == Head.BACKWARDS:
            self.head = Head.FORWARDS
        else:
            raise ValueError("self.HEAD is of incorrect value and/or type.")

    def scan_for_line(self) -> bool:
        # Using infrared detectors
        ir_line = GPIO.input(self.IR01) + GPIO.input(self.IR02) + GPIO.input(self.IR03)
        return ir_line == 3  # > 1

    def oscillate_simple(self):
        def drive(pwm_magnitudes):
            motor_values = [self.head.value * int(num) for num in pwm_magnitudes]
            PWM.setMotorModel(*motor_values)

        base_speed = 1500  # DriveInstructions.BASE.value
        fwd_motor_values = [base_speed] * 4

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
                PWM.setMotorModel(*([new_speed] * 4))
                time.sleep(0.2)
            self.reverse_head()

        # to scale alignment accordingly to the speed the PID was tested with (1000):
        def calculate_align_coeff(current_speed):
            return (current_speed / 1000) ** 0.5
        align_period = self.aligner.sample_time
        previous_align = time.time()
        align_coeff = calculate_align_coeff(base_speed)



        previous_reversal = previous_align
        reversal_period = 2  # seconds  # * calculate_align_coeff(base_speed)
        reversible = True

        i = 0
        while True:
            i += 1
            current_time = time.time()

            if current_time - previous_align >= align_period:  # if i % 5 == 0:
                previous_align = current_time
                align_value = self.aligner.get_direction_correction(base_speed)
                align_value *= align_coeff


                # Clamp the alignment, to limit it from stopping a set of wheels completely, or even reversing the
                # direction.
                align_value = clamp(align_value, -base_speed, base_speed)

                # Split the "burden" of alignment in two parts:
                # One side drives faster, another drives slower, compared to base_speed.
                # Will result in less sudden changes of PWM in a set of wheels, and also be closer to "base speed"
                align_half = align_value / 2
                if self.direction == Direction.RIGHT:
                    fwd_motor_values = [base_speed + align_half] * 2 + \
                                       [base_speed - align_half] * 2
                elif self.direction == Direction.LEFT:
                    fwd_motor_values = [base_speed - align_half] * 2 + \
                                       [base_speed + align_half] * 2
            ir_line = self.scan_for_line()
            # print(ir_line)
            if not ir_line:
                reversible = True

            if (current_time - previous_reversal >= reversal_period) and \
                    ir_line and \
                    reversible:
                previous_reversal = current_time
                reversible = False
                reversal(base_speed)
            drive(fwd_motor_values)
            if i % 30 == 0:
                print("----")
                print("head:{}".format(self.head))
                print("current speed:{}".format(base_speed))
                print("align_value:{}".format(align_value))
                print("fwd_motor_values:{}".format(fwd_motor_values))
                print("p, i, d: {}, {}, {}".format(*self.aligner.pid.components))


if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        driver = LineReversalDriver(Direction.LEFT)
        driver.oscillate_simple()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
        print_exc()
    finally:
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
