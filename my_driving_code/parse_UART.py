# from multiprocessing import Process
from threading import Thread

import serial
import time
from enum import Enum
from os.path import exists, join
from os import mkdir


class DriveInstructions(Enum):
    SLOWER = 1000
    SLOW = 1750
    BASE = 2500
    FAST = 3250
    FASTER = 4000
    BEGIN = 0
    NONE = None


# TODO: Add logging
# Which logs the EWMA data and actions taken, along with time passed since initializing the logger.
# Prints to a new file every time (Check if file_name_# exists, if yes then check file_name_(#+1) and so on).

class Logger:
    def __init__(self):
        self.dir = "data_logs/"
        if not exists(self.dir):
            mkdir(self.dir)
        path_i = 0
        self.file_name = "data_log_{i}.csv".format(i=path_i)
        while exists(join(self.dir, self.file_name)):
            path_i += 1
            self.file_name = "data_log_{i}.csv".format(i=path_i)

        self.file_path = join(self.dir, self.file_name)

        self.NA = "N/A"  # not available tag
        self.delimiter = ";"
        self.file_columns = ["timestamp", "ewma", "instruction"]
        with open(self.file_path, "w") as file:
            file.write(self.delimiter.join(self.file_columns))
            file.write("\n")
        self.start_time = time.time()

    def log(self, input_ewma: int = None, input_instruction: DriveInstructions = None):
        with open(self.file_path, "a+") as file:
            seconds_since_start = int(time.time() - self.start_time)
            line = [str(seconds_since_start), str(input_ewma), input_instruction.name]
            line = self.delimiter.join(line) + "\n"
            file.write(line)


class UART_Comm:
    def __init__(self, port_name):
        self.run_async = False
        self.ser = serial.Serial(port_name, baudrate=115200, timeout=5)
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
        self.recent_ewma = None

        self.reader_thread = Thread(target=self.async_reading, args=())
        self.logger = Logger()

    def reboot_launchpad(self):
        with self.ser as ser:
            ser.write(b'\nreboot\n')
        time.sleep(self.timeout_after_action)

    def set_coordinator(self):
        with self.ser as ser:
            ser.write(b'\nrpl-set-root 1\n')
        print("coordinator started")
        time.sleep(self.timeout_after_action)

    def async_reading(self):
        while self.run_async:
            with self.ser as ser:
                messages = ser.readlines()
                for line in messages:
                    content = line.decode().strip()
                    print("Line:{}".format(content))
                    if ("[DRIVE]: ") in content:
                        instruction_txt = content.replace("[DRIVE]: ", "")
                        instruction = self.instruction_dict[instruction_txt]
                        if instruction != DriveInstructions.NONE:
                            self.recent_instruction = instruction
                    elif ("[DATA]: ") in content:
                        data_txt = content.replace("[DATA]: ", "")
                        if ("EWMA: ") in data_txt:
                            ewma_txt = data_txt.replace("EWMA: ", "")
                            self.recent_ewma = int(ewma_txt)
            if self.recent_instruction != DriveInstructions.NONE and \
                    self.recent_ewma is not None:
                self.logger.log(self.recent_ewma, self.recent_instruction)

    def start_async(self):
        print("Starting Async.")
        self.run_async = True
        self.reader_thread.start()

    def finish_async(self):
        print("Finishing Async.")
        self.run_async = False
        time.sleep(3)
        self.reader_thread.join()

    def read_from_UART(self) -> DriveInstructions:

        start_time = time.time()
        instruction = DriveInstructions.NONE
        # n_lines = 5

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
        # print("duration of read_function:{}".format(time.time() - start_time))
        return instruction


if __name__ == '__main__':
    print('Program is starting ... ')
    port_name = "COM11"
    ser = serial.Serial(port_name, baudrate=115200, timeout=5)
    with ser:
        ser.write(b'\nreboot\n')
        time.sleep(5)
        ser.write(b'\nrpl-set-root 1\n')
