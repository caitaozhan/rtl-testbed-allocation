'''The server doing binary search will call this program
'''

import argparse
import time
from subprocess import Popen, PIPE
from test_interfere import TestInterfere

if __name__ == '__main__':

    hint = 'python binary_search_helper.py -t 10'

    parser = argparse.ArgumentParser(description='this is the program that the binary search program will call ' + hint)
    parser.add_argument('-t', '--time', type=int, nargs=1, default=[10], help='time for rx to sense text')
    parser.add_argument('-f', '--file', type=str, nargs=1, default=['file_receive'], help='the filename that where the receiver store received text')
    args = parser.parse_args()

    # step 1: do some sensing
    rx_time = args.time[0]
    filename = args.file[0]
    command = ['python', 'rx_text.py']
    p = Popen(command)
    try:
        for i in range(rx_time):
            print i
            time.sleep(1)
        p.kill()
    except:
        p.kill()  # if exception occured, make sure the rtlsdr subprocess will be killed

    # step 2: check whether there is interference
    testinter = TestInterfere(filename)
    interfere = testinter.test_interfere(rx_time - 6)
    print(interfere)