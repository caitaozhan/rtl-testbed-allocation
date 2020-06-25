'''Make training easier (receiver side)
   Automate the process of 'python rx-sense.py + move' four times.
'''

import os
import platform
import time
import argparse
from default_config import DEFAULT
from all_rx import AllRx
from utility import Utility
from binarysearch import BinarySearch


if __name__ == "__main__":

    # python training_allo.py

    parser = argparse.ArgumentParser(description = 'Receiver starts sensing RSS samples and save them to a file.')
    parser.add_argument('-si',  '--sample_iteration', type=int, nargs=1, default = [DEFAULT.rx_sample_iter], help = 'how many rss sampling iterations. -1 means unlimited iterations')
    parser.add_argument('-sl',  '--sleep', type=float, nargs=1, default=[DEFAULT.rx_sleep], help = 'how much time to sleep between two sample iterations')
    parser.add_argument('-avg', '--average', type=int, nargs=1, default=[DEFAULT.loc_per_hypothesis], help='averaging: how many locations per hypothesis')
    parser.add_argument('-wt',  '--wait', type=int, nargs=1, default=[DEFAULT.wait_between_loc], help='time for moving the cart')
    parser.add_argument('-ts', '--timestamp', action='store_true', help='whether need to send timestamp')
    args = parser.parse_args()

    sample_iteration = args.sample_iteration[0]
    sleep   = args.sleep[0]
    average = args.average[0]
    wait    = args.wait[0]
    timestamp = args.timestamp

    command = Utility.get_command('speech')
    binarySearch = BinarySearch(debug=False)
    while True:
        raw_input('Press to start a hypothesis')
        for i in range(1, average+1):
            speech = '{} \"{} starts\"'.format(command, i)
            os.system(speech)
            # print('optimal gain is', binarySearch.search(0, 47))
            AllRx.sense(sample_iteration, sleep, timestamp)
            speech = '{} \"{} ends\"'.format(command, i)
            os.system(speech)
            time.sleep(1)
            if i == average:
                os.system('{} \"Press to start new\"'.format(command))
                time.sleep(2)
            else:   # move the cart
                for j in range(wait, 0, -1):
                    speech = '{} {}'.format(command, j)
                    os.system(speech)
                    time.sleep(1)

