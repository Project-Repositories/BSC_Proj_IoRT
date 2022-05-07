import serial
import time
from enum import Enum


class DriveInstructions(Enum):
    SLOWER = 1000
    SLOW = 1750
    BASE = 2500
    FAST = 3250
    FASTER = 4000
    BEGIN = 0
    NONE = None


class UART_Comm:
    def __init__(self, port_name):
        self.ser = serial.Serial(port_name, baudrate=115200, timeout=3)
        self.instruction_dict = {"slow down2": DriveInstructions.SLOWER,
                                 "slow down1": DriveInstructions.SLOW,
                                 "base": DriveInstructions.BASE,
                                 "accelerate1": DriveInstructions.FAST,
                                 "accelerate2": DriveInstructions.FASTER,
                                 "begin": DriveInstructions.BEGIN
                                 }
        self.timeout_after_action = 1
        self.reboot_launchpad()

    def reboot_launchpad(self):
        with self.ser as ser:
            ser.write(b'\nreboot\n')

        # led.colorWipe(led.strip, Color(255, 255, 51))  # Yellow wipe
        time.sleep(self.timeout_after_action)
        print("after reboot: {}".format(self.read_from_UART()))

    def set_coordinator(self):
        with self.ser as ser:
            ser.write(b'reboot\n')
        time.sleep(self.timeout_after_action)

    def read_from_UART(self) -> DriveInstructions:
        instruction = DriveInstructions.NONE
        n_lines = 5
        
        with self.ser as ser:
            messages = []
            for n in range(n_lines):
                messages += [ser.readline().decode().strip()]
            # messages = ser.readall().decode()
            # messages = messages.split('\n')
            print(messages)
            for line in messages:
                content = line.strip()
                if ("[DRIVE]: ") in content:
                    instruction_txt = content.replace("[DRIVE]: ", "")
                    instruction = self.instruction_dict.get(instruction_txt, default=DriveInstructions.NONE)
        return instruction
