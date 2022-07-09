import time
from typing import Union

from PCA9685 import PCA9685


class Motor:
    def __init__(self):
        self.pwm = PCA9685(0x40, debug=True)
        self.pwm.setPWMFreq(50)

    def duty_range(self, duty1, duty2, duty3, duty4):
        if duty1 > 4095:
            duty1 = 4095
        elif duty1 < -4095:
            duty1 = -4095

        if duty2 > 4095:
            duty2 = 4095
        elif duty2 < -4095:
            duty2 = -4095

        if duty3 > 4095:
            duty3 = 4095
        elif duty3 < -4095:
            duty3 = -4095

        if duty4 > 4095:
            duty4 = 4095
        elif duty4 < -4095:
            duty4 = -4095
        return duty1, duty2, duty3, duty4

    def left_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(0, 0)
            self.pwm.setMotorPwm(1, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(1, 0)
            self.pwm.setMotorPwm(0, abs(duty))
        else:
            self.pwm.setMotorPwm(0, 4095)
            self.pwm.setMotorPwm(1, 4095)

    def left_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(3, 0)
            self.pwm.setMotorPwm(2, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(2, 0)
            self.pwm.setMotorPwm(3, abs(duty))
        else:
            self.pwm.setMotorPwm(2, 4095)
            self.pwm.setMotorPwm(3, 4095)

    def right_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(6, 0)
            self.pwm.setMotorPwm(7, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(7, 0)
            self.pwm.setMotorPwm(6, abs(duty))
        else:
            self.pwm.setMotorPwm(6, 4095)
            self.pwm.setMotorPwm(7, 4095)

    def right_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(4, 0)
            self.pwm.setMotorPwm(5, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(5, 0)
            self.pwm.setMotorPwm(4, abs(duty))
        else:
            self.pwm.setMotorPwm(4, 4095)
            self.pwm.setMotorPwm(5, 4095)

    def set_motor_model(self, duty1, duty2=None, duty3=None, duty4=None):
        duty1, duty2, duty3, duty4 = self.duty_range(duty1, duty2, duty3, duty4)
        self.left_Upper_Wheel(-duty1)
        self.left_Lower_Wheel(-duty2)
        self.right_Upper_Wheel(-duty3)
        self.right_Lower_Wheel(-duty4)

    def set_motor_model_by_iterable(self, motor_values_iterable: Union[tuple[int], list[int]]):
        """
        Wrapper of Motor.set_motor_model which takes a single iterable, instead of 4 parameters.
        """
        if len(motor_values_iterable) != 4:
            raise ValueError("setMotorPWM needs an iterable with 4 values, one for each wheel, in the order of "
                             "LEFT FORWARD, LEFT BACKWARD, RIGHT FORWARD, RIGHT BACKWARD")
        else:
            self.set_motor_model(*motor_values_iterable)


# Use the PWM object from this module to use the Motor class.
# This way, it's the same object being mutated.
PWM = Motor()


def loop():
    PWM.set_motor_model(2000, 2000, 2000, 2000)  # Forward
    time.sleep(3)
    PWM.set_motor_model(-2000, -2000, -2000, -2000)  # Back
    time.sleep(3)
    PWM.set_motor_model(-500, -500, 2000, 2000)  # Left
    time.sleep(3)
    PWM.set_motor_model(2000, 2000, -500, -500)  # Right
    time.sleep(3)
    PWM.set_motor_model(0, 0, 0, 0)  # Stop


def destroy():
    PWM.set_motor_model(0, 0, 0, 0)


if __name__ == '__main__':
    try:
        loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()
