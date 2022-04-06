import serial
import time as time
from multiprocessing import Process
from multiprocessing.sharedctypes import Value


def demo_UART(port_name):
    while True:
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
            time.sleep(5)


def async_func(truth):
    print("ASYNC function begin")
    time.sleep(5)
    truth.value = 0
    print("ASYNC function done")
    return

def demo_multi_prcessing():
    print("STARTING DEMO: MULTI_PROCESSING")

    t = Value('i',1,lock=False)
    p = Process(target=async_func, args=(t,))
    count = 0
    p.start()
    while t.value:
        print(f"{count = }")
        count += 1
        time.sleep(1)
    print("ENDING DEMO: MULTI_PROCESSING")

    p.join()


if __name__ == '__main__':
    port_name = "COM8"
    # demo_UART(port_name)
    demo_multi_prcessing()
