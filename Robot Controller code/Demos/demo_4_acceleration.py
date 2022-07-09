import RPi.GPIO as GPIO
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import clamp, NodeType, Timer, Tracking, DriveInstructions, speed_state_dict, acc_state_dict
from Hardware_Controllers.parse_UART import UARTCommunication


class ActiveConnectivityAccelerationLineDriver:
    def __init__(self, inverse_IR: bool, node_type: NodeType):
        self.inverse_IR = inverse_IR
        self.tracker = LineTracker(inverse_IR)

        self.node_type = node_type
        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UARTCommunication(port_name)
        if self.node_type == NodeType.Coordinator:
            self.launchpad_comm.set_coordinator()

    def ac_line_driving_2(self):
        """
        This implementation of Active Connectivity modifies
        the acceleration of the robots depending on the connection strength.
        """
        current_acc = 0
        acc_update_period = 0.5
        acc_timer = Timer(acc_update_period)
        min_speed = speed_state_dict[DriveInstructions.SLOWER]
        max_speed = speed_state_dict[DriveInstructions.FASTER]
        current_speed = 0

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

        current_speed = speed_state_dict[DriveInstructions.BASE]
        debug_i = 0
        while True:
            debug_i += 1

            # ------ communication ------
            if self.node_type == NodeType.Child:
                if read_timer.check():
                    instruction = self.launchpad_comm.recent_instruction
                    if instruction != DriveInstructions.NONE:
                        current_acc = acc_state_dict[instruction]

            # ------ alignment ------
            alignment = self.tracker.get_alignment()

            # ------ fundamental driving ------
            if acc_timer.check():  # If we should update the speed by acceleration amount.
                current_speed += current_acc
                # Clamp it, so that we don't start to reverse, or go too fast for the line tracking to work.
                current_speed = clamp(current_speed, min_speed, max_speed)

            if alignment == Tracking.FORWARD.value:
                # If we are driving forwards, we can use the current speed.
                motor_values = [current_speed] * 4
            else:
                # Else, if we should turn to stay on the line.
                motor_values = alignment
            PWM.set_motor_model_by_iterable(motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("current speed:{}".format(current_speed))
                print("current acceleration:{}".format(current_acc))
                print("fwd_motor_values:{}".format(*motor_values))


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
        driver = ActiveConnectivityAccelerationLineDriver(arg_inverse, arg_nodetype)
        driver.ac_line_driving_2()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.set_motor_model(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        driver.launchpad_comm.finish_async()
        driver.launchpad_comm.reboot_launchpad()
