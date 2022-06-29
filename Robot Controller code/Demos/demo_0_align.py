import time
from Hardware_Controllers.Motor import PWM
from Hardware_Controllers.servo import Servo

from traceback import print_exc # For debugging, to print the entire exception when errors occur, but also handle it gracefully

from Misc_Code.commons import clamp, Head, DriveInstructions
from Control_Programs.wall_alignment import WallAligner, Direction


class AlignDriver:
    """
    Aligns itself to a wall to it's right or left, depending on direction parameter.
    Drives forward for some time, then reverses after a set duration.

    """

    def __init__(self, direction: Direction):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23

        self.direction = direction # Direction.LEFT
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

        turn_time = 2 # Change in favor of optically reading reversal point.
        seconds_per_read = 9  # A message is sent every 10 seconds. We see if there's a new one every 9 seconds.
        previous_turn = previous_read = time.time()

        # to scale alignment accordingly to the speed the PID was tested with (1000):
        def calculate_align_coeff(current_speed):
            return (current_speed / 1000) ** 0.5

        base_speed = DriveInstructions.BASE.value
        fwd_motor_values = [base_speed] * 4

        align_coeff = calculate_align_coeff(base_speed)
        align_value = 0

        i = 0
        while True:
            i += 1
            current_time = time.time()
            if current_time - previous_turn >= turn_time:
                previous_turn = current_time
                reversal(base_speed)

            if current_time - previous_read >= seconds_per_read:
                previous_read = current_time
                instruction = self.launchpad_comm.read_from_UART()
                if instruction != DriveInstructions.NONE:
                    base_speed = instruction.value
                    align_coeff = calculate_align_coeff(base_speed)

            # TODO: Change this to be a set time frequency
            if i % 5 == 0:
                # Only evaluate alignment every 5 iterations.
                # As far as i understand, if PID is evaluated and used too often,
                # the Derivative term becomes useless. Because its effect only lasts for a fraction of a second.
                align_value = self.aligner.get_direction_correction(base_speed)
                align_value *= align_coeff
                # align_value *= 0.1

                # Clamp the alignment, to limit it from stopping a set of wheels completely, or even reversing the
                # direction.
                align_value = clamp(align_value, -base_speed, base_speed)

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
                print("current speed:{}".format(base_speed))
                print("align_value:{}".format(align_value))
                print("fwd_motor_values:{}".format(fwd_motor_values))
                print("p, i, d: {}, {}, {}".format(*self.aligner.pid.components))
            drive(fwd_motor_values)


if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        driver = AlignDriver(Direction.RIGHT)
        driver.oscillate_simple()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
        print_exc()
    finally:
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
