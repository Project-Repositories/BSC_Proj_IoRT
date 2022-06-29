from simple_pid import PID


def test_pid():
    tst_value = 10
    target_value = 0
    pid = PID(1, 0, 0.0, setpoint=target_value)

    def err_map_test(inp):
        if inp > 0:
            inp *= 1000
        else:
            inp *= -250
        return inp

    pid.error_map = err_map_test

    for i in range(5):
        if i % 2:
            i *= -1
        control = pid(i)
        tst_value = tst_value + control
        if i % 1 == 0:
            print("control = {}".format(control))
            print("tst_value = {}".format(tst_value))

if __name__ == '__main__':
    print('Program is starting ... ')
    test_pid()