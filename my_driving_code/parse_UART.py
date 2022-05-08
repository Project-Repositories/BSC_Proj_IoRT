# from multiprocessing import Process
from threading import Thread


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
        self.run_async = False
        self.ser = serial.Serial(port_name, baudrate=115200, timeout=10)
        self.instruction_dict = {"slow down2": DriveInstructions.SLOWER,
                                 "slow down1": DriveInstructions.SLOW,
                                 "base": DriveInstructions.BASE,
                                 "accelerate1": DriveInstructions.FAST,
                                 "accelerate2": DriveInstructions.FASTER,
                                 "begin": DriveInstructions.BEGIN,
                                 }
        self.timeout_after_action = 3
        self.reboot_launchpad()

        self.recent_instruction = DriveInstructions.NONE
        self.reader = Thread(target=self.async_reading, args=())

    def reboot_launchpad(self):
        with self.ser as ser:
            ser.write(b'\nreboot\n')

        # led.colorWipe(led.strip, Color(255, 255, 51))  # Yellow wipe
        # print("after reboot: {}".format(self.read_from_UART()))
        time.sleep(self.timeout_after_action)
        

    def set_coordinator(self):
        with self.ser as ser:
            ser.write(b'\nrpl-set-root 1\n')
        print("coordinator started")
        time.sleep(self.timeout_after_action)


    def async_reading(self):
        while self.run_async:
            with self.ser as ser:
                # message = ser.readline().decode().strip()
                # print("msg is: {}".format(message))
                print("before blocking")
                messages = ser.readlines()
                print("after blocking")
                # messages = messages.split('\n')
                for line in messages:
                    content = line.decode().strip()
                    print("Line:{}".format(content))
                    if ("[DRIVE]: ") in content:
                        instruction_txt = content.replace("[DRIVE]: ", "")
                        instruction = self.instruction_dict[instruction_txt]
                        # self.instruction_dict.get(instruction_txt, DriveInstructions.NONE)
                        if instruction != DriveInstructions.NONE:
                            self.recent_instruction = instruction
            # if instruction != DriveInstructions.NONE:
            #    self.recent_instruction = instruction


    def start_async(self):
        print("Starting Async.")
        self.run_async = True
        self.reader.start()

    def finish_async(self):
        print("Finishing Async.")
        self.run_async = False
        self.reader.join()

    def read_from_UART(self) -> DriveInstructions:
        
        start_time = time.time()
        instruction = DriveInstructions.NONE
        n_lines = 5
        
        with self.ser as ser:
            # messages = []
            # for n in range(n_lines):
            #     messages += [ser.readline().decode().strip()]
            messages = ser.readall().decode()
            messages = messages.split('\n')
            print(messages)
            for line in messages:
                content = line.strip()
                if ("[DRIVE]: ") in content:
                    instruction_txt = content.replace("[DRIVE]: ", "")
                    instruction = self.instruction_dict.get(instruction_txt, DriveInstructions.NONE)
        print("duration of read_function:{}".format(time.time() - start_time))
        return instruction
