import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import NodeType, Timer, Tracking, DriveInstructions,  speed_state_dict
from Hardware_Controllers.parse_UART import UARTCommunication


class ActiveConnectivityLineDriver:
    def __init__(self, inverse_IR: bool, node_type: NodeType):
        self.inverse_IR = inverse_IR
        self.tracker = LineTracker(inverse_IR)

        self.node_type = node_type
        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UARTCommunication(port_name)
        if self.node_type == NodeType.Coordinator:
            self.launchpad_comm.set_coordinator()

    def ac_line_driving(self):
        """
           This implementation of Active Connectivity modifies
           the speed of the robots depending on the connection strength.
        """
        # ------ communication ------
        read_period = 4  # A message is sent every 5 seconds. We see if there's a new one every 4 seconds.
        read_timer = Timer(read_period)

        self.launchpad_comm.start_async()
        instruction = DriveInstructions.NONE
        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                print("checking latest message")
                instruction = self.launchpad_comm.recent_instruction
        forward_speed = speed_state_dict[instruction]

        debug_i = 0
        while True:
            debug_i += 1

            # ------ communication ------
            if read_timer.check():
                instruction = self.launchpad_comm.recent_instruction
                if instruction != DriveInstructions.NONE:
                    forward_speed = speed_state_dict[instruction]

            # ------ alignment ------
            alignment = self.tracker.get_alignment()
            if alignment == Tracking.FORWARD.value:
                motor_values = [forward_speed] * 4
            else:
                motor_values = alignment
            PWM.set_motor_model_by_iterable(motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("Recent instruction:{}".format(instruction))
                print("current speed:{}".format(forward_speed))


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
        driver.ac_line_driving()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.set_motor_model(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        driver.launchpad_comm.finish_async()
        driver.launchpad_comm.reboot_launchpad()
