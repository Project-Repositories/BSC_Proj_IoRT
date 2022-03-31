# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import serial


def demo_UART(port_name):
    ser = serial.Serial(port_name, baudrate=115200, timeout=20)
    s = ser.read(100)  # read up to one hundred bytes
    line = ser.readline()
    print(f"{s.split()[-1:-10:-1] = }")
    # , parity=serial.PARITY_EVEN, rtscts=1


if __name__ == '__main__':
    demo_UART('COM8')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
