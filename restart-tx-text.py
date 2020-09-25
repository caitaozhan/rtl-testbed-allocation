'''
Restart tx-text.py with a new location and/or gain
'''

from argparse import ArgumentParser
from subprocess import Popen
from utility import Utility

if __name__ == '__main__':

    parser = ArgumentParser(description='Restart tx-text.py with a new location and/or gain')
    parser.add_argument('-x', '--x', type=int, nargs=1, default=[0], help='x axis')
    parser.add_argument('-y', '--y', type=int, nargs=1, default=[0], help='y axis')
    parser.add_argument('-g', '--gain', type=int, nargs=1, default=[40], help='gain')
    parser.add_argument('-o', '--off', action='store_true', help='turn off the PU')
    args = parser.parse_args()

    x = args.x[0]
    y = args.y[0]
    gain = args.gain[0]
    off = args.off

    # step 1: find the pid
    program = ' tx-text.py'
    pids = Utility.find_pid(program)

    # step 2: kill the previous program if pid is not -1
    if pids != -1:
        for pid in pids:
            command = 'kill {}'.format(pid).split()
            p = Popen(command)
            print('{} killed'.format(pid))
    # step 3: run the tx-text.py program with new arguments passed in
    if off:
        command = 'python tx-text.py -o'.split()
    else:
        command = 'python tx-text.py -x {} -y {} -g {}'.format(x, y, gain).split()
    p = Popen(command)
