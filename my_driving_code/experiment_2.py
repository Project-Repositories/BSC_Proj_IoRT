from time import sleep
from Motor import PWM
from line_tracker import LineTracker
from servo import Servo
from Led import led

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from commons import Timer, Tracking, DriveInstructions, speed_state_dict, led_off, led_yellow, led_green
from parse_UART import UART_Comm, Logger

PWM.setMotorModel(0, 0, 0, 0)
Servo().setServoPwm('0', 90)
Servo().setServoPwm('1', 90)
"""
Qualitative experiment serving as proof-of-concept of IoRT testbed.
This experiment will have
    - 1 car called the "leading car"
    - 1 car called the "station car"
    - leading car use line tracking
    - Communicate between the 2 cars using TI launchpad.
    - "Leading car" serves as the TSCH coordinator and RPL root.
    - "Station car" serves as a child node.
    - Act based on the Received Signal Strength Indicator (RSSI).

Procedure:
    * Both cars are initially stationary.
    * When connection is formed between the cars, the leading car begins driving at a slow speed,
        adjusting its direction with sharp turns to track a line of tape.
    * The cars frequently sends messages between each other (1 msg each, every 10seconds).
    * When the leading car measures the RSSI    below a certain threshold, it stops driving.
    * The current status of the cars are displayed using the color of their LEDs.
No data is stored during this experiment. The result will be a video recording of the car.

The point of the experiment is 
    to show the cars acting mechanically, depending on some property of their connection.
"""


class E2LeadingCar:
    def __init__(self, inverse_IR: bool, RSSI_termination_threshold: int, RSSI_strong_threshold: int):
        self.tracker = LineTracker(inverse_IR)

        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UART_Comm(port_name, default_logging=False)
        experiment_2_lead_logger = "exp_2_lead_data"
        self.launchpad_comm.logger = Logger(file_name=experiment_2_lead_logger)

        self.launchpad_comm.set_coordinator()

        self.RSSI_termination_threshold = RSSI_termination_threshold
        self.RSSI_strong_threshold = RSSI_strong_threshold

        led.colorWipe(led.strip, led_off)

    def start(self):

        led.colorWipe(led.strip, led_yellow)

        # ------ fundamental driving ------
        current_speed = speed_state_dict[DriveInstructions.SLOW]

        # ------ communication ------
        # A message is sent every 5 seconds. We see if there's a new one every 4 seconds.
        read_period = 4
        read_timer = Timer(read_period)

        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        self.launchpad_comm.start_async()
        instruction = DriveInstructions.NONE  # DriveInstructions.NONE
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                print("checking latest message")

                instruction = self.launchpad_comm.recent_instruction
        print("*" * 3 + " Leading car starting " + "*" * 3)

        led.colorWipe(led.strip, led_green)

        debug_i = 0
        while self.launchpad_comm.recent_ewma > self.RSSI_termination_threshold:
            debug_i += 1

            # ------ alignment ------
            alignment = self.tracker.get_tracking()

            # ------ fundamental driving ------
            if alignment == Tracking.FORWARD:
                # If we are driving forwards, we can use the current speed.
                motor_values = [current_speed] * 4
            else:
                # Else, if we should turn to stay on the line.
                motor_values = alignment.value
            PWM.setMotorModel(*motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("current speed:{}".format(current_speed))
                print("fwd_motor_values:{}".format(*motor_values))

        print("Leading car is stopping.")
        led.colorWipe(led.strip, led_yellow)
        while self.launchpad_comm.recent_ewma < self.RSSI_strong_threshold:
            sleep(2)

        print("Connection-strength has been bolstered.")
        led.colorWipe(led.strip, led_green)
        sleep(10)
        print("Program was completed.")


class E2FollowingCar:
    def __init__(self, inverse_IR: bool, RSSI_termination_threshold: int, RSSI_strong_threshold: int):
        self.tracker = LineTracker(inverse_IR)

        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UART_Comm(port_name, default_logging=False)
        experiment_2_follow_logger = "exp_2_follow_data"
        self.launchpad_comm.logger = Logger(file_name=experiment_2_follow_logger)

        self.RSSI_termination_threshold = RSSI_termination_threshold
        self.RSSI_strong_threshold = RSSI_strong_threshold

        led.colorWipe(led.strip, led_off)

    def start(self):

        led.colorWipe(led.strip, led_yellow)

        # ------ communication ------
        # A message is sent every 5 seconds. We see if there's a new one every 4 seconds.
        read_period = 4
        read_timer = Timer(read_period)

        # Wait until a DriveInstruction is received,
        # which indicates that a connection between node and coordinator has been formed
        self.launchpad_comm.start_async()
        instruction = DriveInstructions.NONE  # DriveInstructions.NONE
        while instruction == DriveInstructions.NONE:
            if read_timer.check():
                print("checking latest message")
                instruction = self.launchpad_comm.recent_instruction

        led.colorWipe(led.strip, led_green)

        while self.launchpad_comm.recent_ewma > self.RSSI_termination_threshold:
            sleep(2)

        led.colorWipe(led.strip, led_yellow)

        # ------ fundamental driving ------
        current_speed = speed_state_dict[DriveInstructions.SLOW]

        print("Following car is catching up.")
        debug_i = 0
        while self.launchpad_comm.recent_ewma < self.RSSI_strong_threshold:
            debug_i += 1
            # ------ alignment ------
            alignment = self.tracker.get_tracking()

            # ------ fundamental driving ------
            if alignment == Tracking.FORWARD:
                # If we are driving forwards, we can use the current speed.
                motor_values = [current_speed] * 4
            else:
                # Else, if we should turn to stay on the line.
                motor_values = alignment.value
            PWM.setMotorModel(*motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("current speed:{}".format(current_speed))
                print("fwd_motor_values:{}".format(*motor_values))

        print("Connection-strength has been bolstered.")
        led.colorWipe(led.strip, led_green)
        sleep(10)
        print("Program was completed.")


# TODO: add more options for Command Line Arguments, such as  direction.
if __name__ == '__main__':
    print('Program is starting ... ')

    arg_RSSI_termination_threshold = -65
    arg_RSSI_strong_threshold = -50

    sysargs = [arg.strip().lower() for arg in sys.argv]
    if "inverse" in sysargs:
        arg_inverse = True
    else:
        arg_inverse = False

    if "child" in sysargs:
        car = E2FollowingCar(arg_inverse, arg_RSSI_termination_threshold, arg_RSSI_strong_threshold)
        print("." * 10 + "\nStarting follower car.\n" + "." * 10)
    else:
        car = E2LeadingCar(arg_inverse, arg_RSSI_termination_threshold, arg_RSSI_strong_threshold)
        print(("." * 10 + "\nStarting Leading car. IR inverse: {}\n" + "." * 10).
              format(arg_inverse))
    try:
        car.start()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.setMotorModel(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        car.launchpad_comm.finish_async()
        car.launchpad_comm.reboot_launchpad()
        sleep(3)
        led.colorWipe(led.strip, led_off)
