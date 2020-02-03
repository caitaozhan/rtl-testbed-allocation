'''Testing phase in realtime.
'''
import os
import sys
import time
import glob
import datetime
import argparse
from collections import defaultdict
from subprocess import Popen, PIPE
import requests
import numpy as np
from default_config import DEFAULT, IndoorMap, OutdoorMap
from collect_rx_data import CollectRx
from collect_tx_data import CollectTx
from all_rx import AllRx
from utility import Utility

try:
    sys.path.append('../Localization')
    from input_output import Input
except ImportError as e:
    print(e)


class RealtimeSupport:
    '''A class that supports the realtime localization (testing phase)
    '''
    def __init__(self, MAP):
        self.map = MAP
        self.ip_2_hostname = {}
        self.init_ip_2_hostname()


    def init_ip_2_hostname(self):
        '''Init a dict of {ip --> hostname} for both Rx and Tx
        '''
        with open(DEFAULT.ser_rx_ip_host_file, 'r') as f:
            for line in f:
                line = line.split(':')
                self.ip_2_hostname[line[0]] = line[1].strip()
        for tx_ip_host in glob.glob(DEFAULT.ser_tx_ip_host_file + '.*'):
            with open(tx_ip_host, 'r') as f:
                for line in f:
                    line = line.split(':')
                    self.ip_2_hostname[line[0]] = line[1].strip()


    def clean_rx_data_tx_log(self):
        '''Clean the rx data under rx_data directory. Since the IP of sensors might change. Also clean tx_log
        '''
        cwd = os.getcwd()
        os.chdir((DEFAULT.ser_rx_data_dir))
        for rx_ip in glob.glob('*.*.*.*'):
            os.remove(rx_ip)
        os.chdir(cwd)

        cwd = os.getcwd()
        os.chdir((DEFAULT.ser_tx_log_dir))
        for rx_ip in glob.glob('*.*.*.*'):
            os.remove(rx_ip)
        os.chdir(cwd)


    def read_rss_data(self):
        '''Read the RSS data from the files created by get_rss_data,
           return a dict of {hostname --> RSS}
        Return:
            {str --> float}
        '''
        # read all Rx data, a dict of {hostname --> [ (datetime, RSS) ]}
        rx_data = defaultdict(list)
        cwd = os.getcwd()
        os.chdir(DEFAULT.ser_rx_data_dir)
        for rx_ip in glob.glob('*.*.*.*'):
            hostname = self.ip_2_hostname[rx_ip]
            with open(rx_ip, 'r') as f:
                for line in f:
                    line = line.split(',')
                    dt = datetime.datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                    rss = float(line[1].strip())
                    rx_data[hostname].append((dt, rss))
        os.chdir(cwd)
        sensordata = {}
        for hostname, dt_rss_list in rx_data.items():
            if len(dt_rss_list) == 0:
                raise Exception(hostname + ' has no RSS')
            rss_list = []
            for dt, rss in dt_rss_list:
                rss_list.append(rss)
            sensordata[hostname] = round(np.mean(rss_list), 6)
        return sensordata


    def read_tx_truth(self):
        '''Read the ground truth of Tx: location and power
        Return:
            {str --> list<float>}
        '''
        try:
            tx_data = {}
            cwd = os.getcwd()
            os.chdir(DEFAULT.ser_tx_log_dir)
            for tx_ip in glob.glob('*.*.*.*'):
                hostname = self.ip_2_hostname[tx_ip]
                locations = []
                with open(tx_ip, 'r') as f:
                    for line in f:
                        if line == '\n':
                            continue
                        line = line.split('|')
                        hostname_tmp = line[0].strip()
                        if hostname_tmp.find(hostname) == -1:
                            raise Exception('Hostname does not match {} and {}'.format(hostname, hostname_tmp))
                        if hostname_tmp != hostname:
                            print(hostname + ' is not transmitting')
                            break
                        x, y = Utility.extract_location(line[2].strip())
                        gain = line[3].strip()
                        locations.append([x, y])
                if len(locations) != 0:   # it can be empty
                    tx_data[hostname] = {"location": list(np.mean(locations, axis=0)), "gain": gain}
        finally:
            os.chdir(cwd)
        return tx_data

    def test_server(self, ip):
        '''Test whether the localization server is on
           When it is not on, then it will throw an exception
        Args:
            ip -- str -- IP address of localization server
        '''
        url = 'http://{}:5000/on'.format(ip)
        requests.get(url=url)

        url = 'http://{}:5001/on'.format(ip)
        requests.get(url=url)


if __name__ == '__main__':

    hint = "python realtime_testing.py -num 1 -src testbed-indoor -met our splot -avg 4 -wt 2 -ip 130.245.70.30 -en 1"

    parser = argparse.ArgumentParser(description='Client side for real time multi-tx localization: sense Rx and send data to server. | Hint: {}'.format(hint))
    parser.add_argument('-num', '--num_intruder', type=int, nargs=1, default=[1], help='num of intruder')
    parser.add_argument('-src', '--data_source', type=str, nargs=1, default=['testbed-indoor'], help='data source: testbed-indoor, testbed-outdoor')
    parser.add_argument('-met', '--method', type=str, nargs='+', default=['our'], help='methods: splot, our, cluster')
    parser.add_argument('-avg', '--average', type=int, nargs=1, default=[DEFAULT.loc_per_hypothesis], help='averaging: how many locations per hypothesis')
    parser.add_argument('-wt',  '--wait', type=int, nargs=1, default=[DEFAULT.wait_between_loc], help='time for moving the cart')
    parser.add_argument('-ip', '--server_ip', type=str, nargs=1, default=['127.0.0.1'], help='the IP address of the localization server')
    parser.add_argument('-en', '--exp_number', type=int, nargs=1, default=[1], help='experiment number, affect the figure numbers')
    args = parser.parse_args()

    num_intruder = args.num_intruder[0]
    data_source  = args.data_source[0]
    methods = args.method
    average = args.average[0]
    wait    = args.wait[0]
    server_ip  = args.server_ip[0]
    exp_number = args.exp_number[0]

    if data_source == 'testbed-indoor':
        realtime = RealtimeSupport(IndoorMap)
    elif data_source == 'testbed-outdoor':
        realtime = RealtimeSupport(OutdoorMap)
    else:
        raise ValueError("testbed invalid!")

    realtime.clean_rx_data_tx_log()
    myinput = Input(num_intruder=num_intruder, data_source=data_source, methods=methods)

    counter = exp_number
    ps = []
    while True:
        try:
            raw_input('Press to start one instance of localization\n')
            myinput.experiment_num = counter

            # step 0: test whether the localization server is on
            realtime.test_server(server_ip)

            # step 1: tell Rx to sense some data, collect Rx sensing data.
            start = time.time()
            for i in range(1, average+1):
                speech = 'spd-say \"{} starts\"'.format(i)
                os.system(speech)
                AllRx.sense(sample_iter=1, sleep=0.1)
                speech = 'spd-say \"{} ends\"'.format(i)
                os.system(speech)
                time.sleep(1)

                if i < average:
                    for j in range(wait, 0, -1):
                        speech = 'spd-say {}'.format(j)
                        os.system(speech)
                        time.sleep(1)
            print('Time for sensing = {}'.format(time.time() - start))

            # step 2: collect RSS data from sensors
            start = time.time()
            CollectRx.get_rss_data(num_samples=average)
            myinput.sensor_data = realtime.read_rss_data()
            print('time on collecting RSS data from Rx = {}'.format(time.time() - start))

            # step 3: collect Tx ground truth
            start = time.time()
            CollectTx.get_tx_log(DEFAULT.ser_tx_usernames, mode='test', num_log=2)
            myinput.ground_truth = realtime.read_tx_truth()
            print('time on collecting Tx log = {}'.format(time.time() - start))

            # step 4: use curl to send a request to localization server
            curl = "curl -d \'{}\' -H \'Content-Type: application/json\' -X POST http://{}:{}/localize"
            command = curl.format(myinput.to_json_str(), server_ip, 5000)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append(p)

            command = curl.format(myinput.to_json_str(), server_ip, 5001)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append(p)

            for p in ps:
                if p.poll() is not None: # has respond from server
                    # do something
                    ps.remove(p)
            counter += 1
        except KeyboardInterrupt:
            break
        except Exception as e:
            print('Error! ', e)
