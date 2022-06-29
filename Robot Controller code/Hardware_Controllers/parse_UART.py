# from multiprocessing import Process
from threading import Thread

import serial
import time
from os.path import exists, join
from os import mkdir

from Misc_Code.commons import DriveInstructions
from random import randint


# TODO: Add logging
# Which logs the EWMA data and actions taken, along with time passed since initializing the logger.
# Prints to a new file every time (Check if file_name_# exists, if yes then check file_name_(#+1) and so on).

class Logger:
    def __init__(self, file_name="data_log"):
        self.dir = "../data_logs/"
        if not exists(self.dir):
            mkdir(self.dir)
        path_i = 0
        self.file_ext = ".csv"
        self.full_file_name = "{name}_{i}{ext}".format(name=file_name, i=path_i,ext=self.file_ext)
        while exists(join(self.dir, self.full_file_name)):
            path_i += 1
            self.full_file_name = "{name}_{i}{ext}".format(name=file_name, i=path_i, ext=self.file_ext)

        self.file_path = join(self.dir, self.full_file_name)

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


class ActiveConnectivity:
    def __init__(self):
        self.speed_changed = self.acc_changed = self.brake = self.accelerate = False
        self.EWMA = self.EWMA_tmp = None
        self.weak_threshold = -35
        self.strong_threshold = self.weak_threshold + 5
        self.worsen_threshold = 3

        self.alpha = 0.75
        self.instruction = DriveInstructions.BASE

    def calibrate_ewma(self, new_RSSI):
        if self.EWMA is None:
            self.EWMA = new_RSSI
        else:
            self.EWMA = (self.alpha * new_RSSI) + (1 - self.alpha) * self.EWMA

    def ACR(self, new_RSSI):
        """
        Active Connectivity Random choice
        """
        self.calibrate_ewma(new_RSSI)
        if self.EWMA <= self.weak_threshold:
            if not self.speed_changed:
                self.EWMA_tmp = self.EWMA
                self.speed_changed = True

                if randint(0, 1):
                    self.brake = True
                    self.accelerate = False
                    self.instruction = DriveInstructions.SLOW
                else:
                    self.brake = False
                    self.accelerate = True
                    self.instruction = DriveInstructions.FAST

        """ If RSSI decreased, meaning we chose the wrong action: """
        if self.speed_changed and \
                (self.EWMA_tmp - self.EWMA >= self.worsen_threshold):
            if not self.acc_changed:
                self.acc_changed = True
                if self.accelerate:
                    self.accelerate = False
                    self.brake = True
                    self.instruction = DriveInstructions.SLOWER
                elif self.brake:
                    self.accelerate = True
                    self.brake = False
                    self.instruction = DriveInstructions.FASTER
        """
        RSSI has returned to 'sufficient' values after a speed change:
        """
        if self.EWMA >= self.strong_threshold and self.speed_changed:
            self.brake = self.accelerate = False
            self.acc_changed = self.speed_changed = False
            self.instruction = DriveInstructions.BASE


class UART_Comm:
    def __init__(self, port_name, default_logging=True):
        self.run_async = False
        self.ser = serial.Serial(port_name, baudrate=115200, timeout=2)
        self.instruction_dict = {"slow down2": DriveInstructions.SLOWER,
                                 "slow down1": DriveInstructions.SLOW,
                                 "base": DriveInstructions.BASE,
                                 "accelerate1": DriveInstructions.FAST,
                                 "accelerate2": DriveInstructions.FASTER,
                                 "begin": DriveInstructions.BEGIN,
                                 }
        self.timeout_after_action = 3
        self.reboot_launchpad()

        self.ac = ActiveConnectivity()

        self.recent_instruction = DriveInstructions.NONE
        self.recent_ewma = None

        self.reader_thread = Thread(target=self.async_reading, args=())
        if default_logging:
            self.logger = Logger()
        else:
            self.logger = None

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
                    if ("[DATA]: ") in content:
                        data_txt = content.replace("[DATA]: ", "")
                        if ("RSSI: ") in data_txt:
                            rssi_txt = data_txt.replace("RSSI: ", "").strip()
                            rssi = float(rssi_txt)
                            self.ac.ACR(rssi)
                            self.recent_instruction = self.ac.instruction
                            self.recent_ewma = self.ac.EWMA
                            print("EWMA is: {}".format(self.recent_ewma))

            if self.logger is None:
                continue
            elif self.recent_instruction == DriveInstructions.NONE:
                continue
            elif self.recent_ewma is None:
                continue
            else:
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
