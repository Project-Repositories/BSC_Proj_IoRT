# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import serial
import time as time


def demo_UART(port_name):
    with serial.Serial(port_name, baudrate=115200, timeout=5) as ser:
        line = ser.readline()
        content = line.decode()
        content = content.strip()
        # content = content.split('\n')[-1:-3:-1]
        # content = [txt.strip() for txt in content]
        if content != "[INFO: TSCH      ] scanning on channel 20":
            print(f"{content = }")
        else:
            print("t")
        # , parity=serial.PARITY_EVEN, rtscts=1


if __name__ == '__main__':
    while True:
        demo_UART('COM8')
        time.sleep(5)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
