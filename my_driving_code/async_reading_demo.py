import time
import traceback
from multiprocessing import Manager

from parse_UART import UART_Comm

if __name__ == '__main__':
    print('Program is starting ... ')
    port_name = "COM8"
    comm = UART_Comm(port_name)
    comm.start_async()
    i = 0
    try:
        while True:
            print(i)
            print("most recent instruction: {}".format(comm.recent_instruction))
            i += 1
            time.sleep(5)
    except KeyboardInterrupt as e:
        print("Program terminated")
    finally:
        comm.finish_async()
