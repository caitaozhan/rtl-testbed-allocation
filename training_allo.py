'''Make training easier (receiver side)
   Automate the process of 'python rx-sense.py + move' four times.
'''

import os
import platform
import time
import argparse
import glob
import numpy as np
import threading
import Queue
from collections import defaultdict
from default_config import DEFAULT
from all_rx import AllRx
from utility import Utility
from binarysearch import BinarySearch
from collect_rx_data import CollectRx
from collect_tx_data import CollectTx


class RecordTrainingSample:
    '''One line of a sample: 
        Type 1 PU1loc, PU1power, ..., PUnloc, PUnpower, SU location, SU optimal power
        Type 2 SS1 power, ..., SSn power, SU location, SU optimal power  
    '''
    def __init__(self, type1, type2):
        self.type1_file = type1
        self.type2_file = type2
        self.ip_2_hostname = {}
        self.init_ip_2_hostname()


    def init_ip_2_hostname(self):
        with open(DEFAULT.ser_rx_ip_host_file, 'r') as f:
            for line in f:
                line = line.split(':')
                self.ip_2_hostname[line[0]] = line[1].strip()

    def record_type1(self, pu_info, su_opt_gain, su_loc):
        ''' PU data and SU data
        Args:
            pu_info  -- list<dict>
            opt_gain -- int
            su_loc   -- tuple<int, int>
        '''
        pu_dict = {}
        for pu in pu_info:
            pu_dict[pu['hostname']] = pu
        pu_list = ['T1', 'T2', 'T3', 'T4']
        with open(self.type1_file, 'a') as f:
            for pu in pu_list:
                if pu in pu_dict and pu_dict[pu]['tx_on'] == 'True':
                    f.write('{}, {}, {}, '.format(pu_dict[pu]['x'], pu_dict[pu]['y'], pu_dict[pu]['gain']))
                else:
                    f.write('nan, nan, nan, ')
            f.write('{:.1f}, {:.1f}, {}\n'.format(float(su_loc[0]), float(su_loc[1]), su_opt_gain))


    def record_type2(self, opt_gain, su_loc):
        ''' SS data and SU data
        Args:
            opt_gain -- int
            su_loc   -- tuple<int, int>
        '''
        rx_data = defaultdict(list)
        cwd = os.getcwd()
        os.chdir(DEFAULT.ser_rx_data_dir)
        for rx_ip in glob.glob('*.*.*.*'):
            hostname = self.ip_2_hostname[rx_ip]
            with open(rx_ip, 'r') as f:
                for line in f:
                    line = line.split(',')
                    # dt = datetime.datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                    rss = float(line[1].strip())
                    rx_data[hostname].append(rss)
        os.chdir(cwd)
        sensors = ['host-101', 'host-102', 'host-104', 'host-105', 'host-110', 'host-120', 'host-130', 'host-140', 'host-150', 'host-158', 'host-160', 'host-166', 'host-170', 'host-180', 'host-188', 'host-190', 'host-200', 'host-210']
        with open(self.type2_file, 'a') as f:
            for s in sensors:
                if not rx_data[s]:
                    print('sensor {} has no data'.format(s))
                    f.write('nan, ')
                else:
                    f.write('{:.2f}, '.format(np.mean(rx_data[s])))
            f.write('{:.1f}, {:.1f}, {}\n'.format(float(su_loc[0]), float(su_loc[1]), opt_gain))


queue_pu  = Queue.Queue()

def ss_sense_record():
    # step 2: do the SS sensing, collect the sensing data, record it
    start = time.time()
    AllRx.sense(sample_iteration, sleep, timestamp)
    CollectRx.get_rss_data(sample_iteration)
    print('SS sensing time = {}'.format(time.time() - start))
    

def pu_info_record():
    # step 3: collect PU info, record it
    start = time.time()
    pu_info = CollectTx.get_pu_info()
    queue_pu.put(pu_info)
    print('get PU info time = {}'.format(time.time() - start))



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
    average = args.average[0]  # not using this variable
    wait    = args.wait[0]
    timestamp = args.timestamp

    command = Utility.get_command('speech')
    binarySearch = BinarySearch(debug=False)
    record = RecordTrainingSample(DEFAULT.su_type1_data, DEFAULT.su_type2_data)
    for _ in range(2):
        speech = '{} \"Move the primary users to new location\"'.format(command)
        os.system(speech)
        for _ in range(2):
            if Utility.test_lwan('192.168.30.') is False:
                print('Not connected to 192.168.30. private net')
                break
            raw_input('Press to start a new binary search')
            speech = '{} \"Change the primary users power\"'.format(command)
            os.system(speech)
            x = raw_input('SU X coordinate = ')
            y = raw_input('SU Y coordinate = ')

            # put previous step 2 & 3 here, run concurrently with step 1
            # t_ss = threading.Thread(target=ss_senserecord)
            # t_ss.start()
            t_pu = threading.Thread(target=pu_info_record)
            t_pu.start()

            # step 1: do binary search
            start = time.time()
            opt_gain = binarySearch.search(0, 47)
            print('optimal gain is', opt_gain, 'time = {:2}'.format(time.time() - start))

            # t_ss.join()
            t_pu.join()

            pu_info = queue_pu.get()
            record.record_type1(pu_info, opt_gain, su_loc=(x, y))
            # record.record_type2(opt_gain, su_loc=(x, y))
