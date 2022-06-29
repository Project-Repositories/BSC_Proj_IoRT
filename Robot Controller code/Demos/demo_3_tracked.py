import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import Head, NodeType, Timer, Tracking, DriveInstructions
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
        self.tracker = LineTracker(inverse_IR)
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


    def oscillate_simple(self):
        # ------ fundamental driving ------
        def drive(pwm_magnitudes):
            motor_values = [self.head.value * int(num) for num in pwm_magnitudes]
            PWM.setMotorModel(*motor_values)

        base_speed = DriveInstructions.BASE.value
        fwd_motor_values = [base_speed] * 4

        # ------ communication ------
        read_period = 9  # A message is sent every 10 seconds. We see if there's a new one every 9 seconds.
        read_timer = Timer(read_period)
        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        self.launchpad_comm.start_async() 
        instruction = DriveInstructions.BASE  # DriveInstructions.NONE
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                print("checking latest message") 
                instruction = self.launchpad_comm.recent_instruction
                if instruction != DriveInstructions.NONE:
                    base_speed = instruction.value
                # instruction = self.launchpad_comm.read_from_UART()
                # print("Waiting for instruction to drive. ")

        debug_i = 0
        while True:
            debug_i += 1

            # ------ communication ------
            if read_timer.check():
                instruction = self.launchpad_comm.recent_instruction
                if instruction != DriveInstructions.NONE:
                    base_speed = instruction.value

            # ------ alignment ------
            alignment = self.tracker.get_tracking()

            # ------ fundamental driving ------
            if alignment == Tracking.FORWARD:
                motor_values = [base_speed] * 4 #  [instruction.value] * 4
                # print("t1")
            else:
                motor_values = alignment.value
                # print("t2")
            PWM.setMotorModel(*motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("head:{}".format(self.head))
                print("current speed:{}".format(base_speed))
                print("fwd_motor_values:{}".format(fwd_motor_values))


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
