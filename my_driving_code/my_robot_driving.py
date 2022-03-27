import Ultrasonic as ul
from Motor import *

from Led import *
from rpi_ws281x import * # to get the Color() class, I think.

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
if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        led.colorWipe(led.strip, Color(255, 0, 0))  # Red wipe
        # TODO: Send message to LP to begin TSCH
        # TODO: read messages from LP using PySerial
        # TODO: wait until LP tells us TSCH is ready (another device connected
        led.colorWipe(led.strip, Color(0, 255, 0))  # Green wipe
        # TODO: Begin running the driving code (ultrasonic or linetracking)
        # periodically check the latest message of the LP.

        ultrasonic.run()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        ultrasonic.PWM.setMotorModel(0, 0, 0, 0)
        ultrasonic.pwm_S.setServoPwm('0', 90)

        led.colorWipe(led.strip, Color(0, 0, 0))  # turn off LED


