'''The binary search helper is ran on the {PU/PUR side}
run time is ~0.1 second
'''

import argparse
import sys
import os
from subprocess import Popen, PIPE
from test_interfere import TestInterfere
from utility import Utility
from default_config import DEFAULT
import json

if __name__ == '__main__':

    hint = 'python binary_search_helper.py'

    parser = argparse.ArgumentParser(description='this is the program that the binary search program will call ' + hint)
    parser.add_argument('-f', '--file', type=str, nargs=1, default=['file_receive'], help='the filename that where the receiver store received text')
    args = parser.parse_args()
    hostname = os.uname()[1]  # T3

    # step 0: check whether the PU transmitter is on
    if hostname == 'T4' and Utility.program_is_running_t4() is False:  # special ad hoc for T4 ...
        print 'hostname = ', hostname
        print 'PU TX on = ', False
        print 'RX disconnect = ', None
        print 'interfere = ', None
    elif hostname != 'T4' and Utility.program_is_running('tx_text.py') is False and Utility.program_is_running('tx-text.py') is False:
        print 'hostname = ', hostname
        print 'PU TX on = ', False
        print 'RX disconnect = ', None
        print 'interfere = ', None
    else:
        filename = args.file[0]
        testinter = TestInterfere(filename)
        interfere = testinter.test_interfere()
        with open(DEFAULT.pur_info_file, 'r') as f:
            lines = f.readlines()
            pur_info = json.loads(lines[0])
        print 'hostname = ', hostname
        print 'PU TX on = ', True
        print '\nRX disconnect = ', True if pur_info['discon'] == 'True' else False 
        print 'interfere = ', interfere