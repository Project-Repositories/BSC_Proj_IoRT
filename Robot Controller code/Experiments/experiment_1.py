from time import sleep
from Hardware_Controllers.Motor import PWM
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo
from Hardware_Controllers.Led import led

# For command-line arguments
import sys
# For debugging, to print the entire exception when errors occur, but also handle it gracefully
from traceback import print_exc

from Misc_Code.commons import NodeType, Timer, Tracking, DriveInstructions, speed_state_dict, acc_state_dict, \
    led_off, led_red, led_yellow, led_green
from Hardware_Controllers.parse_UART import UARTCommunication, Logger

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
    * When the leading car measures the RSSI below a certain threshold, it stops driving.
    * The current status of the cars are displayed using the color of their LEDs.
There's 2 results from this experiment
    1. A video recording of the car, which shows proof-of-concept of testbed
    2. A logfile which includes the RSSI measurements received during the experiment.

The point of the experiment is 
    to show the cars acting mechanically, depending on some property of their connection.
"""

PWM.set_motor_model(0, 0, 0, 0)
Servo().setServoPwm('0', 90)
Servo().setServoPwm('1', 90)


class E1LeadingCar:
    def __init__(self, inverse_IR: bool, RSSI_termination_threshold: int):
        self.tracker = LineTracker(inverse_IR)

        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UARTCommunication(port_name)
        experiment_1_lead_logger = "exp_1_lead_data"
        self.launchpad_comm.logger = Logger(file_name=experiment_1_lead_logger)

        self.launchpad_comm.set_coordinator()

        self.RSSI_termination_threshold = RSSI_termination_threshold

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
            PWM.set_motor_model(*motor_values)

            # ------ debugging ------
            if debug_i % 100 == 0:
                print("----")
                print("current speed:{}".format(current_speed))
                print("fwd_motor_values:{}".format(*motor_values))

        led.colorWipe(led.strip, led_red)
        PWM.set_motor_model(0, 0, 0, 0)

        print("Program was completed.")
        while True:
            print("stalling... keeps collecting data...")
            sleep(3)


class E1StationCar:
    def __init__(self, RSSI_termination_threshold: int):
        port_name = "/dev/ttyACM0"
        self.launchpad_comm = UARTCommunication(port_name, default_logging=False)
        experiment_1_station_logger = "exp_1_station_data"
        self.launchpad_comm.logger = Logger(file_name=experiment_1_station_logger)

        self.RSSI_termination_threshold = RSSI_termination_threshold

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

        led.colorWipe(led.strip, led_red)
        print("Program was completed.")
        while True:
            print("stalling... keeps collecting data...")
            sleep(3)


if __name__ == '__main__':
    print('Program is starting ... ')

    arg_RSSI_termination_threshold = -65
    sysargs = [arg.strip().lower() for arg in sys.argv]
    if "inverse" in sysargs:
        arg_inverse = True
    else:
        arg_inverse = False

    if "child" in sysargs:
        car = E1StationCar(arg_RSSI_termination_threshold)
        print("." * 10 + "\nStarting station car.\n" + "." * 10)
    else:
        car = E1LeadingCar(arg_inverse, arg_RSSI_termination_threshold)
        print(("." * 10 + "\nStarting Leading car. IR inverse: {}\n" + "." * 10).
              format(arg_inverse))
    try:
        car.start()
    except KeyboardInterrupt:  # Exception as e:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        print("program was terminated.")
    finally:
        print_exc()
        PWM.set_motor_model(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
        car.launchpad_comm.finish_async()
        car.launchpad_comm.reboot_launchpad()
        sleep(3)
        led.colorWipe(led.strip, led_off)
