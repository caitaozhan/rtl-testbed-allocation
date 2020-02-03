'''
Make training easier (transmitter side)
Two mode for indoors:  fixed route of locations, and input locations
One mode for outdoors: gps mode
'''

import time
import argparse
from subprocess import Popen
from default_config import DEFAULT

if __name__ == '__main__':

    hint = 'python tx-run-wrapper.py -n 1 -g 53 -mo test |' +\
           'python tx-run-wrapper.py -n 1 -g 53 -mo train -gps |' +\
           'python tx-run-wrapper.py -n 1 -g 53 -mo train -hrf'


    parser = argparse.ArgumentParser(description='A wrapper for tx-run.py')
    parser.add_argument('-n', '--name', type=int, nargs=1, default=[1], help='the name of the transmitter')
    parser.add_argument('-hrf', '--hackrf', action='store_true', help='Whether is hackrf of usrp, default is false')
    parser.add_argument('-g', '--gain', type = int, nargs = 1, default = [DEFAULT.tx_gain], help = 'Gain of the transmitter')
    parser.add_argument('-gps', '--gps', action='store_true', help='gps is needed in outdoor case')
    parser.add_argument('-mo', '--mode', type=str, nargs=1, default=['train'], help='train mode or test mode')
    args = parser.parse_args()

    tx_name = args.name[0]
    hackrf  = args.hackrf
    gain    = args.gain[0]
    gps     = args.gps
    mode    = args.mode[0]

    freq = DEFAULT.tx_freq

    if gps is False:
        ans = raw_input('Fixed route (mainly for training, check if tx_train_log need cleaning)? (y/n)')
        if ans == 'y':
            x_len = 8
            locations = [(i, 0) for i in range(x_len)]
            locations = locations + [(i, 1) for i in range(x_len-1, -1, -1)]
            locations = locations + [(i, 3) for i in range(x_len)]
            locations = locations + [(i, 4) for i in range(x_len-1, -1, -1)]
            locations = locations + [(i, 5) for i in range(x_len)]
            locations = locations + [(i, 2) for i in range(x_len-1, -1, -1)]
            print('locations to train:', locations)
            start_x = int(raw_input('enter starting point x: '))
            start_y = int(raw_input('enter starting point y: '))
            index = locations.index((start_x, start_y))
            for loc in locations[index:]:
                x, y = loc[0], loc[1]
                raw_input('\npress to start Tx at ({}, {})'.format(x, y))
                try:
                    if hackrf:
                        command = 'sudo python tx-run.py -n {} -hrf -g {} -x {} -y {} -mo {}'.format(tx_name, gain, x, y, mode)
                    else:
                        command = 'sudo python tx-run.py -n {} -g {} -x {} -y {} -mo {}'.format(tx_name, gain, x, y, mode)
                    p = Popen(command, shell=True)
                    p.wait()
                except KeyboardInterrupt:
                    # p.send_signal(signal.SIGINT)  # don't need this, and still works...
                    time.sleep(1)

        elif ans == 'n':
            while True:
                x = raw_input('\nx = ')
                y = raw_input('y = ')
                if x == -1 and y == -1:
                    break
                try:
                    if hackrf:
                        command = 'sudo python tx-run.py -n {} -hrf -g {} -x {} -y {} -mo {}'.format(tx_name, gain, x, y, mode)
                    else:
                        command = 'sudo python tx-run.py -n {} -g {} -x {} -y {} -mo {}'.format(tx_name, gain, x, y, mode)
                    p = Popen(command, shell=True)
                    p.wait()
                except KeyboardInterrupt:
                    # p.send_signal(signal.SIGINT)  # don't need this, and still works...
                    time.sleep(1)
        else:
            print('Please input y or n')
    else: # outdoor with gps mode
        while True:
            raw_input("Press to start new hypothesis")
            try:
                if hackrf:
                    command = 'sudo python tx-run.py -n {} -hrf -g {} -gps -mo {}'.format(tx_name, gain, mode)
                else:
                    command = 'sudo python tx-run.py -n {} -g {} -gps -mo {}'.format(tx_name, gain, mode)
                p = Popen(command, shell=True)
                p.wait()
            except KeyboardInterrupt:
                # p.send_signal(signal.SIGINT)  # don't need this, and still works...
                time.sleep(1)

