import time
from Motor import PWM

max_speed = 3000
current_speed = max_speed
step = 50
if __name__ == '__main__':
    print('Program is starting ... ')
    for i in range(int(max_speed/step * 2)):
        current_speed -= step
        time.sleep(0.01)
        motor_values = [current_speed] * 4
        PWM.setMotorModel(*motor_values)
    PWM.setMotorModel(0,0,0,0)
        