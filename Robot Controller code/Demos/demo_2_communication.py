import time
import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import clamp, Head, NodeType, Timer, DriveInstructions
from Control_Programs.wall_alignment import WallAligner, Direction
from Hardware_Controllers.parse_UART import UART_Comm


class ActiveConnectivityDriver:
    def __init__(self, direction: Direction, nodetype: NodeType):
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

        self.nodetype = nodetype
        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UART_Comm(port_name)
        if self.nodetype == NodeType.Coordinator:
            self.launchpad_comm.set_coordinator()

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
        # ------ fundamental driving ------
        def drive(pwm_magnitudes):
            motor_values = [self.head.value * int(num) for num in pwm_magnitudes]
            PWM.setMotorModel(*motor_values)

        base_speed = 1500  # DriveInstructions.BASE.value
        fwd_motor_values = [base_speed] * 4

        # ------ reversal ------
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

        reversal_period = 1  # seconds  # * calculate_align_coeff(base_speed)
        reversal_timer = Timer(reversal_period)
        reversible = True

        # ------ alignment ------
        # to scale alignment accordingly to the speed the PID was tested with (1000):
        def calculate_align_coeff(current_speed):
            return (current_speed / 1000) ** 0.5

        align_period = self.aligner.sample_time
        align_timer = Timer(align_period)
        align_coeff = calculate_align_coeff(base_speed)
        align_value = 0

        # ------ communication ------
        read_period = 9  # A message is sent every 10 seconds. We see if there's a new one every 9 seconds.
        read_timer = Timer(read_period)
        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        instruction = DriveInstructions.NONE
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                instruction = self.launchpad_comm.read_from_UART()
                print("Waiting for instruction to drive. ")

        debug_i = 0
        while True:
            debug_i += 1

            # ------ communication ------
            if read_timer.check():
                instruction = self.launchpad_comm.recent_instruction
                if instruction != DriveInstructions.NONE:
                    base_speed = instruction.value
                    align_coeff = calculate_align_coeff(base_speed)

            # ------ alignment ------
            if align_timer.check():
                align_value = self.aligner.get_direction_correction(base_speed)
                align_value *= align_coeff

                # Clamp the alignment, to limit it from stopping a set of wheels completely, or even reversing the
                # direction.
                align_value = clamp(align_value, -base_speed // 1, base_speed // 1)

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

            # ------ reversal  ------
            ir_line = self.scan_for_line()
            if not ir_line and not reversible:
                reversal_timer = Timer(reversal_period)
                reversible = True

            if (reversal_timer.check()) and \
                    ir_line and \
                    reversible:
                reversible = False
                reversal(base_speed)

            # ------ fundamental driving ------
            drive(fwd_motor_values)

            # ------ debugging ------
            if debug_i % 30 == 0:
                print("----")
                print("head:{}".format(self.head))
                print("current speed:{}".format(base_speed))
                print("align_value:{}".format(align_value))
                print("fwd_motor_values:{}".format(fwd_motor_values))
                print("p, i, d: {}, {}, {}".format(*self.aligner.pid.components))


# TODO: add more options for Command Line Arguments, such as  direction.
if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        sysargs = [arg.strip().lower() for arg in sys.argv]
        if "child" in sysargs:
            arg_nodetype = NodeType.Child
        else:
            arg_nodetype = NodeType.Coordinator

        if "left" in sysargs:
            arg_direction = Direction.LEFT
        else:
            arg_direction = Direction.RIGHT

        print(("." * 10 + "\nStarting driver. {}\n{}\n" + "." * 10).
              format(arg_direction, arg_nodetype))
        driver = ActiveConnectivityDriver(arg_direction, arg_nodetype)
        driver.oscillate_simple()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        driver.launchpad_comm.finish_async()
