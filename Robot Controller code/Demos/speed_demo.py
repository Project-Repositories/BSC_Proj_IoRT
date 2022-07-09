import time
from traceback import print_exc

from Hardware_Controllers.Motor import PWM
from Hardware_Controllers.servo import Servo

if __name__ == '__main__':
    print('Program is starting ... ')
    pwm_list = [600, 1000, 1750, 2500, 3250, 4000]
    duration = 5
    avg_speeds = []


    def drive(pwm_magnitude):
        motor_values = [pwm_magnitude] * 4
        PWM.set_motor_model(*motor_values)


    def test_speed(pwm_magnitude):
        print("Now running car with PWM {magnitude} for {dura} seconds".format(magnitude=pwm, dura=duration))
        drive(pwm_magnitude)
        time.sleep(duration)
        drive(0)


    try:
        for pwm in pwm_list:
            test_speed(pwm)
            user_txt = input("Please enter the distance covered by the robot in cm, then reset its position.\n"
                             "If you want to retry, enter 'r'").strip().lower()
            while user_txt == 'r':
                test_speed(pwm)
                user_txt = input("Please enter the distance covered by the robot in cm, then reset its position.\n"
                                 "If you want to retry, enter 'r'").strip().lower()
            distance = float(user_txt)
            avg_speeds.append(distance / duration)
    finally:
        print("The avg speeds were:")
        for i in range(len(avg_speeds)):
            print("{pwm}: {speed} m/s".format(pwm=pwm_list[i], speed=avg_speeds[i] * 0.01))

        print_exc()
        PWM.set_motor_model(0, 0, 0, 0)
        Servo().setServoPwm('0', 90)
        Servo().setServoPwm('1', 90)
