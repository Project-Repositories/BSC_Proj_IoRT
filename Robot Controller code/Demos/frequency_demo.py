import time

"""
This program was used to evaluate how often i could check conditions in the main 'while' loop
"""

if __name__ == '__main__':
    print('Program is starting ... ')
    print("frequency demo : type 1")
    print("." * 10)
    periods_to_check = [0.05, 0.01, 0.005] # [5, 2, 1, 0.5, 0.25, 0.2, 0.15, 0.10, 0.05]
    n_checks = 10
    for period in periods_to_check:
        avg_time = 0
        for n in range(n_checks):
            check_time = time.time()
            time.sleep(period)
            avg_time += time.time() - check_time
        avg_time = avg_time / n_checks
        print("-" * 3)
        print("average time for period of {}s : {}s.\n deviation of {}s".format(period, avg_time, avg_time - period))

    print("." * 10)
    print("frequency demo : type 2")
    print("." * 10)
    for period in periods_to_check:
        avg_time = 0
        for n in range(n_checks):
            check_time = time.time()
            while time.time() - check_time <= period:
                pass
            avg_time += time.time() - check_time
        avg_time = avg_time / n_checks
        print("-" * 3)
        print("average time for period of {}s : {}s.\ndeviation of {}s".format(period, avg_time, avg_time - period))
