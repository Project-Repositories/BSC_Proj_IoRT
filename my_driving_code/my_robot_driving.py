from multiprocessing import Process, Value

import serial

import Ultrasonic as ul
from Motor import *

from Led import *
from rpi_ws281x import *  # to get the Color() class, I think.
from Line_Tracking import Line_Tracking
from Motor import PWM

"""
Goal:
Initially, have the cars' LED light up with red color.
Using the UART connection and PySerial library, send a message to the Launchpad to begin TSCH protocol.
Read from a config file (we've written) to determine if the car should initially serve as TSCH coordinator.
The config file might also contain other information, such as the name of the serial port ("COM11", for example).
When TSCH is ready (1 (or all) non-coordinator joins the network), the LEDs change to green.
Then, they begin driving. Coordinator might drive at a constant. faster speed than non-coordinators.
When they reach the end of the track, perform action to turn around. The cars must turn around, not just reverse,
as the ultrasonic sensor is necessary to sense the end of the track.
Send small packages between coordinator and non-coordinator constantly. The packets are used to monitor signal strength.
When signal (RSSI) gets weak, perform corrective action (network retopologize, re-calculate pathing, (de-)acceleration).
(Change of topology should happen by sending a message to the launchpad?)
At such a moment, change the LEDs of non-coordinator to yellow.
When signal strength has returned to acceptable values, LED changes to green.
If the connection between nodes is "very weak", change LED to red.
if the connection is completely broken, the LEDs should change to blue (?).

After running x number of laps around the track, the cars should come to a stop.
The cars should keep track of statistics during the course of the program.
When the cars are done driving, the statistics should be written to a file.
This marks the end of the program.

"""

ultrasonic = ul.Ultrasonic()


def reboot_robot(port_name):
    def reboot_launchpad(port_name):
        with serial.Serial(port_name, baudrate=115200, timeout=5) as ser:
            ser.write(b'reboot\n')

    led.colorWipe(led.strip, Color(255, 255, 51))  # Yellow wipe
    reboot_launchpad(port_name)
    time.sleep(5)


def check_rpl_connected(port_name, attempts_left) -> bool:
    if attempts_left == 0:
        return False
    print("\tchecking connection... ")
    with serial.Serial(port_name, baudrate=115200, timeout=1) as ser:
        ser.write(b'rpl-status\n')
        n_attempts = 3  # number of lines to check after writing to launchpad
        for _ in range(n_attempts):
            line = ser.readline()
            line = line.decode()
            line.strip()
            if "--  Instance:" in line:
                rpl_instance = line[line.index(": ") + 2:]
                if rpl_instance == "None":
                    print("\tRPL not connected")
                    return False
                else:
                    print("\tRPL is connected")
                    return True
    time.sleep(1)
    check_rpl_connected(port_name, attempts_left - 1)


def async_connection_check(port_name, is_conn):
    while True:
        is_conn.value = check_rpl_connected(port_name, 1)
        if is_conn.value:
            led.colorWipe(led.strip, Color(0, 255, 0))  # Green wipe
        else:
            led.colorWipe(led.strip, Color(255, 255, 51))  # Yellow wipe
        time.sleep(10)


if __name__ == '__main__':
    print('Program is starting ... ')
    lt = Line_Tracking()
    port = "/dev/ttyACM0"
    is_connected = Value('i', 0, lock=False)
    p_conn_checker = Process(target=async_connection_check, args=(port, is_connected,))
    # periodically check the connection status of the LP.
    try:
        reboot_robot(port)
        p_conn_checker.start()
        while not is_connected.value:   # wait until LP tells us TSCH is ready (another device connected
            print("[Main] Waiting to connect...")
            time.sleep(5)
        print("[Main] Connected to root node!")

        # Begin driving:
        print("[Main] Driving begins")
        lt.oscillate_async(is_connected)  # contains a while-loop, running until the connection stops.
        PWM.setMotorModel(0, 0, 0, 0)
        p_conn_checker.kill()
        led.colorWipe(led.strip, Color(0, 0, 0))  # turn off LED

    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
        p_conn_checker.kill()

        led.colorWipe(led.strip, Color(0, 0, 0))  # turn off LED
