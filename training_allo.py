'''Make training easier (receiver side)
   Automate the process of 'python rx-sense.py + move' four times.
'''

import os
import time
import argparse
import glob
import numpy as np
import threading
import Queue
import random
from subprocess import Popen, PIPE
from collections import defaultdict
from default_config import DEFAULT
from all_rx import AllRx
from utility import Utility
from binarysearch import BinarySearch
from collect_rx_data import CollectRx
from collect_tx_data import CollectTx
from pu import PU


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
        pu_list = ['T1', 'T2', 'T3', 'T4', 'T5']
        with open(self.type1_file, 'a') as f:
            counter = 0
            for pu in pu_list:
                if pu in pu_dict and pu_dict[pu]['tx_on'] == 'True':
                    counter += 1
            f.write('{}, '.format(counter))
            for pu in pu_list:
                if pu in pu_dict and pu_dict[pu]['tx_on'] == 'True':
                    f.write('{}, {}, {}, '.format(pu_dict[pu]['x'], pu_dict[pu]['y'], pu_dict[pu]['gain']))
                else:
                    pass
                    # f.write('nan, nan, nan, ')
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
                    f.write('{:.5f}, '.format(np.mean(rx_data[s])))
            f.write('{:.1f}, {:.1f}, {}\n'.format(float(su_loc[0]), float(su_loc[1]), opt_gain))


queue_pu  = Queue.Queue()

def ss_sense():
    '''do the SS sensing, collect the sensing data, record it
    '''
    AllRx.sense(sample_iteration, sleep, timestamp)

def ss_collect():
    '''collect sensor data
    '''
    start = time.time()
    CollectRx.get_rss_data(sample_iteration)
    print('--> 2.1 SS collect time = {}'.format(time.time() - start))

def pu_info_record():
    '''step 3: collect PU info, record it
    '''
    start = time.time()
    pu_info = CollectTx.get_pu_info()
    queue_pu.put(pu_info)
    print('--> 2.2 get PU info time = {}'.format(time.time() - start))

def enter_pu_loc(pu_list):
    for pu in pu_list:
        pu_x = raw_input('{} x = '.format(pu.name))
        pu_y = raw_input('{} y = '.format(pu.name))
        pu.x, pu.y = pu_x, pu_y
    loc_correct = raw_input('\nIs location correct? y/n = ')
    return loc_correct

def read_pu():
    '''read the info of PU/PUR
    Return:
        a list of PU objects
    '''
    pu_list = []
    with open(DEFAULT.pu_ip_host_file) as f:
        for line in f:
            line = line.split(':')
            tmp_pu = PU(line[0], line[1].strip(), 0, 0, 0, True)
            pu_list.append(tmp_pu)
    return pu_list

def restart_pu(pu_list):
    '''restart the PUs remotely and automatically
    '''
    ps = []
    for pu in pu_list:
        if pu.on is False:
            ssh_command = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python restart-tx-text.py -o'".format(pu.hostname, pu.ip)
        else:
            ssh_command = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python restart-tx-text.py -x {} -y {} -g {}'" \
                          .format(pu.hostname, pu.ip, pu.x, pu.y, pu.gain)
        p = Popen(ssh_command, shell=True, stdout=PIPE)
        ps.append(p)
    time.sleep(7)  # 4 seconds for the restart, 1 second for network delay
    for p in ps:
        p.kill()   # killing the main process doesn't affect the subprocess it created (at the PU side)

def update_on_off(pu_list):
    print 'turning PU on/off ...'
    num_on = random.randint(max(1, int(len(pu_list)/2)), len(pu_list))
    pu_on = sorted(random.sample(range(len(pu_list)), num_on))
    for i in range(len(pu_list)):
        if i in pu_on:
            pu_list[i].on = True
            print '{}'.format(pu_list[i].get_loc())
        else:
            pu_list[i].on = False
            print '{} off '.format(pu_list[i].name)
    print '\n'


if __name__ == "__main__":

    # python training_allo.py

    parser = argparse.ArgumentParser(description = 'Receiver starts sensing RSS samples and save them to a file.')
    parser.add_argument('-si',  '--sample_iteration', type=int, nargs=1, default = [DEFAULT.rx_sample_iter], help = 'how many rss sampling iterations. -1 means unlimited iterations')
    parser.add_argument('-sl',  '--sleep', type=float, nargs=1, default=[DEFAULT.rx_sleep], help = 'how much time to sleep between two sample iterations')
    parser.add_argument('-avg', '--average', type=int, nargs=1, default=[DEFAULT.loc_per_hypothesis], help='averaging: how many locations per hypothesis')
    parser.add_argument('-wt',  '--wait', type=int, nargs=1, default=[DEFAULT.wait_between_loc], help='time for moving the cart')
    parser.add_argument('-ts', '--timestamp', action='store_true', help='whether need to send timestamp')
    parser.add_argument('-su', '--su_type', type=str, nargs=1, default=['hackrf'], help='SU being either hackrf or usrp')
    args = parser.parse_args()

    sample_iteration = args.sample_iteration[0]
    sleep   = args.sleep[0]
    average = args.average[0]  # not using this variable
    wait    = args.wait[0]
    timestamp = args.timestamp
    su_type = args.su_type[0]

    command = Utility.get_command('speech')
    binarySearch = BinarySearch(tx=su_type, debug=False)
    record = RecordTrainingSample(DEFAULT.su_type1_data, DEFAULT.su_type2_data)
    pu_list = read_pu()

    while True:

        if Utility.test_lwan('192.168.30.') is False:
            print 'Not connected to 192.168.30. private net'
            break

        speech = '{} \"Change P U location?\"'.format(command)
        os.system(speech)
        change_pu_loc = raw_input('y/n = ')
        if change_pu_loc == 'y':
            correct = enter_pu_loc(pu_list)
            while correct == 'n':  # in case enter wrong location by mistake
                correct = enter_pu_loc(pu_list)

        speech = '{} \"Enter the S U location\"'.format(command)
        os.system(speech)
        x = raw_input('SU X coordinate = ')
        y = raw_input('SU Y coordinate = ')

        for i in range(DEFAULT.su_same_loc_repeat):
            speech = '{} \"repeat {}\"'.format(command, i)
            os.system(speech)

            update_on_off(pu_list)

            speech = '{} \"Change the P U power\"'.format(command)
            os.system(speech)
            for pu in pu_list:
                if pu.on:
                    pu.generate_gain()
                    print '{} '.format(pu.gain),
                else:
                    print 'off ',
            print ''
            # 0. start the PUs with the new power --> 5 seconds here
            restart_pu(pu_list)

            # 1. start the PUR sensing            --> 7 seconds here (in parallel with sensing)
            print 'start the PUR...'
            pu = binarySearch.read_pu()
            start_PUR_ssh = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python binary_search_prepare.py'"
            for key, val in pu.items():
                Popen(start_PUR_ssh.format(val, key), shell=True, stdout=PIPE)

            # the sensors sense data when only the PUs are turned on
            t_ss = threading.Thread(target=ss_sense)
            start = time.time()
            t_ss.start()
            t_ss.join()
            delta = time.time() - start
            print('--> 1 SS sensing time = {}'.format(delta))
            time.sleep(max(0, 8 - delta))

            # collecting Sensing data and PU info, and binary search happen conccurently
            t_ss = threading.Thread(target=ss_collect)
            t_pu = threading.Thread(target=pu_info_record)
            t_ss.start()
            t_pu.start()

            # do binary search to get the label (the optimal power)
            start = time.time()
            if su_type == 'hackrf':
                opt_gain = binarySearch.search(0, 47)  # around 1 minute
            elif su_type == 'usrp':
                opt_gain = binarySearch.search(21, 70)
            print '--> 2.3 optimal gain is', opt_gain, 'time = {:2}'.format(time.time() - start)

            t_ss.join()
            t_pu.join()

            # step -1: end PUR sensing
            end_PUR_ssh = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python binary_search_prepare_end.py'"
            for key, val in pu.items():
                Popen(end_PUR_ssh.format(val, key), shell=True, stdout=PIPE)
            print('end PUR')
            pu_info = queue_pu.get()
            record.record_type1(pu_info, opt_gain, su_loc=(x, y))
            record.record_type2(opt_gain, su_loc=(x, y))

