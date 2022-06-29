import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import clamp, Head, NodeType, Timer, Tracking, DriveInstructions, speed_state_dict, acc_state_dict
from Hardware_Controllers.parse_UART import UART_Comm


class ActiveConnectivityLineDriver:
    def __init__(self, inverse_IR: bool, nodetype: NodeType):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)

        self.inverse_IR = inverse_IR
        # self.aligner = WallAligner(self.direction)
        self.tracker = LineTracker(inverse_IR)
        self.head = Head.FORWARDS

        self.nodetype = nodetype
        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UART_Comm(port_name)
        if self.nodetype == NodeType.Coordinator:
            self.launchpad_comm.set_coordinator()


    def oscillate_simple(self):
        # ------ fundamental driving ------
        def drive(pwm_magnitudes):
            mtr_values = [self.head.value * int(num) for num in pwm_magnitudes]
            PWM.setMotorModel(*mtr_values)

        current_speed = speed_state_dict[DriveInstructions.BASE]
        fwd_motor_values = [current_speed] * 4

        # Used as a period check of when the speed should be increased/decreased
        current_acc = 0
        acc_update_period = 0.5
        acc_timer = Timer(acc_update_period)
        min_speed = speed_state_dict[DriveInstructions.SLOWER]
        max_speed = speed_state_dict[DriveInstructions.FASTER]

        # ------ communication ------
        read_period = 4  # A message is sent every 5 seconds. We see if there's a new one every 9 seconds.
        read_timer = Timer(read_period)
        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        self.launchpad_comm.start_async()
        instruction = DriveInstructions.NONE  # DriveInstructions.NONE
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                print("checking latest message")
                instruction = self.launchpad_comm.recent_instruction
                if instruction != DriveInstructions.NONE:
                    current_acc = acc_state_dict[instruction]
                # instruction = self.launchpad_comm.read_from_UART()
                # print("Waiting for instruction to drive. ")

        debug_i = 0
        while True:
            debug_i += 1

            # ------ communication ------
            if self.nodetype == NodeType.Child:
                if read_timer.check():
                    instruction = self.launchpad_comm.recent_instruction
                    if instruction != DriveInstructions.NONE:
                        current_acc = acc_state_dict[instruction]

            # ------ alignment ------
            alignment = self.tracker.get_tracking()

            # ------ fundamental driving ------
            if acc_timer.check():  # If we should update the speed by acceleration amount.
                current_speed += current_acc
                # Clamp it, so that we don't start to reverse, or go too fast for the line tracking to work.
                current_speed = clamp(current_speed, min_speed, max_speed)

            if alignment == Tracking.FORWARD:
                # If we are driving forwards, we can use the current speed.
                motor_values = [current_speed] * 4  # [instruction.value] * 4
            else:
                # Else, if we should turn to stay on the line.
                motor_values = alignment.value
            PWM.setMotorModel(*motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("head:{}".format(self.head))
                print("current speed:{}".format(current_speed))
                print("current acceleration:{}".format(current_acc))
                print("fwd_motor_values:{}".format(*motor_values))


# TODO: add more options for Command Line Arguments, such as  direction.
if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        sysargs = [arg.strip().lower() for arg in sys.argv]
        if "child" in sysargs:
            arg_nodetype = NodeType.Child
        else:
            arg_nodetype = NodeType.Coordinator
        if "inverse" in sysargs:
            arg_inverse = True
        else:
            arg_inverse = False

        print(("." * 10 + "\nStarting driver. IR inverse: {}\n{}\n" + "." * 10).
              format(arg_inverse, arg_nodetype))
        driver = ActiveConnectivityLineDriver(arg_inverse, arg_nodetype)
        driver.oscillate_simple()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        driver.launchpad_comm.finish_async()
        driver.launchpad_comm.reboot_launchpad()
