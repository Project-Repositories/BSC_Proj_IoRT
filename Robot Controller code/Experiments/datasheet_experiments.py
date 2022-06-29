import sys
import time

from Hardware_Controllers.Motor import PWM
from Hardware_Controllers.Ultrasonic import Ultrasonic
from Misc_Code.commons import Timer, Tracking
from Control_Programs.line_tracker import LineTracker
from Hardware_Controllers.servo import Servo

"""
Auxiliary functions
"""


def turn_off_car():
    PWM.setMotorModel(0, 0, 0, 0)
    Servo().setServoPwm('0', 85)
    Servo().setServoPwm('1', 85)


turn_off_car()

"""
Experiment functions
"""

""" 
Speed experiments.
Results are observed by video-recording the car during the experiments, 
then using LoggerPro to analyze the video. 

The results of these experiments depends highly on the surface that the robot is being tested on, 
which influences the friction coefficient, etc.
"""


def max_speed_experiment():
    """
    The max speed is derived by providing the motors with the highest possible PWM.
    Then, we apply the aforementioned "speed-experiment" procedure to find the maximum speed in m/s.
    """
    duration = 5
    timer = Timer(duration)
    max_PWM = 4095
    PWM.setMotorModel(max_PWM, max_PWM, max_PWM, max_PWM)
    while not timer.check():
        pass
    turn_off_car()


def min_speed_experiment():
    """
    The minimum functioning speed is experimentally derived.
    Initially, attempt to drive the car using very low PWM.
    Then increase the PWM until it actually begins moving.
    Afterwards, use the usual speed-experiment method to find the speed in m/s.
    """
    duration = 5
    timer = Timer(duration)
    min_PWM = 500
    PWM.setMotorModel(min_PWM, min_PWM, min_PWM, min_PWM)
    while not timer.check():
        pass
    turn_off_car()


def line_track_max_speed_experiment():
    """
    Similarly to the min_speed_experiment, the maximum functioning line-tracking speed is experimentally derived.
    We begin with the highest possible PWM.
    Then, we manually decrease it, until the car can actually follow along the line.
    Afterwards, we use the usual speed-experiment method to find the speed in m/s.
    """
    duration = 5
    timer = Timer(duration)
    max_PWM = 4095

    tracker = LineTracker(inverse_light=True)
    while not timer.check():
        # ------ alignment ------
        alignment = tracker.get_tracking()

        # ------ fundamental driving ------
        if alignment == Tracking.FORWARD:
            # If we are driving forwards, we can use the current speed.
            motor_values = [max_PWM] * 4
        else:
            # Else, if we should turn to stay on the line.
            motor_values = alignment.value
        PWM.setMotorModel(*motor_values)
    turn_off_car()


"""
Maneuverability experiments
These experiments are used to determine how good the robot is at changing direction.
The general method is the same as for speed experiments - we use LoggerPro to analyze the results.
"""


def turn_speed_experiment():
    """
    This experiment is to find out how quickly the robot can rotate using our standard method for turning.
    """
    duration = 5
    timer = Timer(duration)
    # ------ alignment ------
    turn_values = Tracking.RIGHT2.value
    PWM.setMotorModel(*turn_values)
    while not timer.check():
        pass
    turn_off_car()


def direction_flip_speed_experiment():
    """
    The name of this experiment does not immediately make its purpose obvious.
    The experiment lets the robot drive at its max speed forward,
    then reverses the direction, and drives at its max speed backwards.
    The point is to figure out how quickly the robot can accelerate.
    """
    duration = 1.5
    timer = Timer(duration)
    max_PWM = 4095
    PWM.setMotorModel(max_PWM, max_PWM, max_PWM, max_PWM)
    while not timer.check():
        pass
    max_PWM = -4095
    PWM.setMotorModel(max_PWM, max_PWM, max_PWM, max_PWM)
    while not timer.check():
        pass
    turn_off_car()


def brake_length_experiment():
    """
    The purpose of this experiment is to find how far the robot will continue moving when going from 100% to 0%.
    The code used for this experiment is identical to the max_speed_experiment.
    The main difference will be where our camera is placed, and what we analyze using logger pro.
    """
    max_speed_experiment()


def climb_steep_terrain_experiment():
    """
    The purpose of this experiment is to find how steep a road the robot can climb.
    The idea is to initially use the maximum tracking speed.
    Then, we use a sort of platform which we can measure and increment the steepness of.
    The platform will have a tracking line for the robot to follow.
    When the angle is too steep, so the robot cannot drive on it, we increase the PWM provided.
    The final angle (hopefully at PWM=4095) will be the maximum steepness of the robot.
    """
    pass


def sonic_range():
    """
    The purpose of this experiment is to find the range of the ultrasonic sensor.
    We repeatedly measure and print the distance of the sensor.
    Following this, we point the sensor towards something very far away.
    It should be able to give us a reading. But to verify if it's correct,
    slightly change the angle and see if the measurement changes.
    If it does not change, then we reduce the distance towards the object,
    until we get valid measurements.
    """

    ul = Ultrasonic()
    try:
        while True:
            distance = ul.get_distance()
            print("distance of UltraSonicSensor: {}".format(distance))
            time.sleep(3)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        turn_off_car()


def battery_life():
    """
    The purpose of this experiment is to find how long the robot can continuously drive before the
    energy levels of the battery is too low to function.
    We begin by fully charging the battery, and noting the current time at the start of the experiment.
    Then, we make the robot drive back and forth in an enclosed space, at its minimum speed.
    When the robot stops moving, we note how much time has passed.
    """
    duration = 0.5
    timer = Timer(duration)
    try:
        while True:
            max_PWM = 4095
            PWM.setMotorModel(max_PWM, max_PWM, max_PWM, max_PWM)
            while not timer.check():
                pass
            max_PWM = -4095
            PWM.setMotorModel(max_PWM, max_PWM, max_PWM, max_PWM)
            while not timer.check():
                pass

    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        turn_off_car()



if __name__ == '__main__':
    print('Program is starting ... ')

    try:
        sysargs = [arg.strip().lower() for arg in sys.argv]
        if "maxspeed" in sysargs:
            max_speed_experiment()
        elif "minspeed" in sysargs:
            min_speed_experiment()
        elif "maxtrack" in sysargs:
            line_track_max_speed_experiment()
        elif "turnspeed" in sysargs:
            turn_speed_experiment()
        elif "fliptime" in sysargs:
            direction_flip_speed_experiment()
        elif "maxtrack" in sysargs:
            line_track_max_speed_experiment()
        elif "brakelength" in sysargs:
            brake_length_experiment()
        elif "sonicrange" in sysargs:
            sonic_range()
        elif "batterylife" in sysargs:
            battery_life()
        elif "off" in sysargs:
            turn_off_car()
    finally:
        print("Program completed.")
        turn_off_car()
