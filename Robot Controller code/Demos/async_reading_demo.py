import time

from Hardware_Controllers.parse_UART import UARTCommunication


if __name__ == '__main__':
    print('Program is starting ... ')
    port_name = "COM8"
    comm = UARTCommunication(port_name)
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
