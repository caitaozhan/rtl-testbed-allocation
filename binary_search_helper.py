'''The binary search helper is ran on the {PU/PUR side}
'''

import argparse
import time
import sys
import os
from subprocess import Popen, PIPE
from test_interfere import TestInterfere
from utility import Utility
from default_config import DEFAULT


if __name__ == '__main__':

    hint = 'python binary_search_helper.py -t 10'

    parser = argparse.ArgumentParser(description='this is the program that the binary search program will call ' + hint)
    parser.add_argument('-t', '--time', type=int, nargs=1, default=[10], help='time for rx to sense text')
    parser.add_argument('-f', '--file', type=str, nargs=1, default=['file_receive'], help='the filename that where the receiver store received text')
    parser.add_argument('-de', '--debug', action='store_true', help='print stderr')
    args = parser.parse_args()

    hostname = os.uname()[1]  # T3
    debug = args.debug

    # step 0: check whether the transmitter is on
    if Utility.program_is_running('tx_text.py') is False:
        print 'hostname = ', hostname
        print 'PU TX on = ', False
        print 'RX disconnect = ', None
        print 'interfere = ', None
    else:
        # step 0: let the file_transmit.py running
        command = ['python', 'file_transmit.py', '-n', hostname[1:]]
        p_file_transmit = Popen(command, stdout=PIPE)

        # step 1: do some sensing
        rx_time = args.time[0]
        filename = args.file[0]
        command = ['python', 'rx_text_ssh.py']
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        try:
            for i in range(rx_time):
                print i,
                sys.stdout.flush()
                time.sleep(1)
            print ''
            p.kill()
        except:
            p.kill()  # if exception occured, make sure the rtlsdr subprocess will be killed

        stderr = p.stderr.readlines()
        stderr = ' '.join(stderr)
        if debug:
            print(stderr)

        rx_disconnect = False
        if stderr.find('UHD Error') != -1:
            rx_disconnect = True

        # step 2: check whether there is interference
        testinter = TestInterfere(filename)
        interfere = testinter.test_interfere(rx_time - 6, DEFAULT.success_rate, DEFAULT.success_rate)
        print 'hostname = ', hostname
        print 'PU TX on = ', True
        print '\nRX disconnect = ', rx_disconnect
        print 'interfere = ', interfere

        p_file_transmit.kill()
    