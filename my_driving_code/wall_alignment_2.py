import time
from enum import Enum
from servo import Servo
from Ultrasonic import Ultrasonic
from simple_pid import PID
from Motor import PWM
import RPi.GPIO as GPIO


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
        self.pwm_Servo.setServoPwm('0',self.direction.value)
        time.sleep(0.25)  # Wait until servo has moved
        # Measure the initial distance to wall:
        self.target_distance = self.ultrasonic.get_distance()
        print("target distance: {}".format(self.target_distance))

        # Needs to be evaluated experimentally:
        self.pid = PID(-50, -0.5, -100, setpoint=0) # -50, -0.5, -25
        # TODO: Set the negative bound to larger magnitude; possibly -150
        self.pid.output_limits = (-1000, 1000)

    def get_direction_correction(self, speed_magnitude: int):
        # calculate error by measuring difference of current distance to target distance:
        
        distance_error = self.ultrasonic.get_distance() - self.target_distance

        control_value = self.pid(distance_error)
        controlled_wheel_magnitude = ((100 + control_value) / 100 ) * speed_magnitude 
        if False:
            print(("distance_error: {0}\n" +
            "control_value: {1}\n" +
            "controlled_wheel_magnitude: {2}").format(distance_error,
                                                      control_value,
                                                      controlled_wheel_magnitude))
        # when distance has increased since start, then control_value > 0, .
            # Turn towards enum direction.
        # When distance has decreased, control_value < 0.
            # Turn away from enum direction.
        return control_value # controlled_wheel_magnitude


class SimpleDriver:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01, GPIO.IN)
        GPIO.setup(self.IR02, GPIO.IN)
        GPIO.setup(self.IR03, GPIO.IN)
        
        self.direction = Direction.RIGHT
        self.aligner = WallAligner(self.direction)

    def turn_left(self, base_speed, turn_speed):
        turn_speed = int(abs(turn_speed) * (-1))
        base_speed = int(base_speed)
        motor_values = ([turn_speed] * 2) + ([base_speed] * 2)
        PWM.setMotorModel(*motor_values)
        time.sleep(0.25)

    def turn_right(self, base_speed, turn_speed):
        turn_speed = int(abs(turn_speed) * (-1))
        base_speed = int(base_speed)
        motor_values = ([base_speed] * 2) + ([turn_speed] * 2)
        PWM.setMotorModel(*motor_values)
        time.sleep(0.25)


    def oscillate_simple(self):
        def drive(direction,fwd_motor_values):
            motor_values = [direction * int(num) for num in fwd_motor_values]
            PWM.setMotorModel(*motor_values)

        direction = 1

        turn_time = 2.5
        align_time = 0.5
        previous_turn = previous_align = time.time()

        base_speed = 1000
        aligned_modifier = 0
        fwd_motor_values = [base_speed] * 4
        
        i = 0
        while True:
            i += 1
            fwd_motor_values = [base_speed] * 4
            current_time = time.time()
            if current_time - previous_turn >= turn_time:
                previous_turn = current_time
                direction *= -1
                drive(direction, [0]*4)
                time.sleep(0.25)
                
            if False: # current_time - previous_align >= align_time:
                previous_align = current_time
                align_modifier = self.aligner.get_direction_correction(base_speed)
                """if self.direction == Direction.LEFT:
                    if align_modifier > 0:
                        align_modifier *= -1
                        fwd_motor_values = ([base_speed] * 2) + ([align_modifier] * 2)
                    else:
                        fwd_motor_values = ([align_modifier] * 2) + ([base_speed] * 2)
                """                    
                if self.direction == Direction.RIGHT:
                    if abs(align_modifier) > 0:
                        
                        align_modifier = align_modifier / 100
                        print("align triggered:{}".format(align_modifier))
                        base_modified = base_speed * abs(align_modifier) 
                        if align_modifier > 0:
                            self.turn_right(base_modified, (align_modifier * base_speed))
                        else:
                            self.turn_left(base_modified, (align_modifier * base_speed))
                    else:
                        pass
                        # fwd_motor_values = ([base_speed] * 2) + ([align_modifier  * base_speed] * 2)
            
            if False: #current_time - previous_align >= align_time:
                align_modifier = self.aligner.get_direction_correction(base_speed)
                previous_align = time.time()
                if align_modifier > 25:
                    
                    PWM.setMotorModel(*([0]*4))
                    time.sleep(0.20)
                    self.turn_right(base_speed * 1.2, -base_speed )
                    # timeout aligner for some more time:
                    previous_align = time.time() + 2.5
            align_value = self.aligner.get_direction_correction(base_speed)

            if direction == 1:
                if align_value > 0: # turn right
                    fwd_motor_values = [base_speed] * 2 + [base_speed - align_value] * 2
                elif align_value < 0:
                    fwd_motor_values = [base_speed + align_value] * 2 + [base_speed ] * 2
            elif direction == -2:
                align_value /= 10
                if align_value < 0:
                    fwd_motor_values = [base_speed] * 2 + [base_speed + align_value] * 2
                elif align_value > 0:
                    fwd_motor_values = [base_speed - align_value] * 2 + [base_speed ] * 2
            if i % 50 == 0:
                print("align_value:{}".format(align_value))
                print("fwd_motor_values:{}".format(fwd_motor_values))
                
            # TODO: Test this out
            # fwd_motor_values = [base_speed] * 2 + [300] * 2
            drive(direction, fwd_motor_values)


def test_pid():
    tst_value = 10
    target_value = 0
    pid = PID(1, 0, 0.0, setpoint=target_value)
    for i in range(100):
        control = pid(tst_value)
        tst_value = tst_value + control
        if i % 10 == 0:
            print("control = {}".format(control))
            print("tst_value = {}".format(tst_value))

if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        driver = SimpleDriver()
        driver.oscillate_simple()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        PWM.setMotorModel(0, 0, 0, 0)
        driver.aligner.pwm_Servo.setServoPwm('0',90)