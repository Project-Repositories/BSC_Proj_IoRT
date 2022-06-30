import time
from enum import Enum
from Hardware_Controllers.servo import Servo
from Hardware_Controllers.Ultrasonic import Ultrasonic
from simple_pid import PID


class Direction(Enum):
    LEFT = 0
    RIGHT = 170


class WallAligner:
    """
    PID explained:
    Ultrasonic sensor chosen to point in either right of left direction.
    Initial distance is measured.
    Then, change in distance to wall in chosen direction is measured.
    By modifying the speed of 2 wheels on the chosen side, we can turn the car
    until the distance is returned to initial condition.
    To turn the car the correct direction,
    an increase in distance should lead to decrease in RPM of chosen wheels.
    This means the PID coefficients should be negative.
    """

    def __init__(self, direction: Direction):
        self.direction = direction
        self.ultrasonic = Ultrasonic()
        self.pwm_Servo = Servo()
        self.pwm_Servo.setServoPwm('0', self.direction.value)
        self.pwm_Servo.setServoPwm('1', 90)
        time.sleep(2)  # Wait until servo has moved

        # Measure the initial distance to wall:
        self.target_distance = self.ultrasonic.get_distance()

        # This is configured experimentally:
        self.pid = PID(-50, -0.5, -20, setpoint=0)
        self.sample_time = 0.15
        self.pid.sample_time = self.sample_time

        # "error mapping" function, which takes the current measured distance
        # then calculates the difference from the target.
        def error_mapping(measured_distance):
            """
            By implementing an error mapping function,
            we can "condemn" a measured distance closer to 0 (robot approaching wall),
            and large measured distances (robot approaching opposite wall, going off course),
            by possibly using exponential or square transformation.
            """
            min_distance = 7
            max_distance = None  # depends on the physical environment

            # PID takes the negative of the input error.
            # This isn't intuitive for our use-case, as measured distance can't be negative.
            measured_distance = abs(measured_distance)
            distance_error = measured_distance - self.target_distance
            if measured_distance < min_distance or (max_distance and measured_distance > max_distance):
                distance_error = distance_error * 1.5
            return -distance_error

        self.pid.error_map = error_mapping

        # The range of PWM for the car wheels are [-4096,4096]. So the output limits should probably be half of this.
        # (only set to avoid "integral windup", since we clamp the PID control value afterwards anyways.)
        max_pwm = 4095
        self.pid.output_limits = (-max_pwm, max_pwm)  # (-max_pwm // 2, max_pwm // 2)  # -1000, 1000

    def get_direction_correction(self):
        """
        When distance has increased since start, then control_value > 0,
        Then, turn towards chosen direction.
        When distance has decreased, control_value < 0.
        Then, turn away from chosen direction.
        """
        # calculate correction by using a PID system with the current distance measurement:
        current_distance = self.ultrasonic.get_distance()
        control_value = self.pid(current_distance)

        return control_value
