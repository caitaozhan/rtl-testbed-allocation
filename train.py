'''
On the localization server side
Given the training data from Rx and transmit log from Tx, do the training: 1) mean 2) std
This .py file contains three class: Train, TxLog, and Hypothesis

'''

import os
import sys
import datetime
import glob
import argparse
import shutil
import json
from subprocess import Popen
from bisect import bisect_right, bisect_left
from collections import defaultdict
import numpy as np
from default_config import DEFAULT, IndoorMap, OutdoorMap
from collect_rx_data import CollectRx
from collect_tx_data import CollectTx
from utility import Utility
from interpolate import Interpolate


try:
    sys.path.append('../Localization')
    from sensor import Sensor
except ImportError as e:
    print('Import errors! ', e)


class Train:
    ''' Basically training is initializing the Hypothesis objects
    '''

    MAP = None

    def __init__(self):
        self.tx_transmit_log = defaultdict(list)     # {loc --> [TxLog]}, at one location, Tx might has multiple activities
        self.hypotheses = {}                         # {loc --> Hypothesis}
        self.location_transform = None               # NOTE why do I need this... ?
        self.train_power = {}
        self.ip_2_hostname = {}
        self.init_train_power()
        self.init_tx_transmit_log()
        self.init_ip_2_hostname()


    def init_tx_transmit_log(self):
        '''Read the Tx transmit log
        '''
        cwd = os.getcwd()
        print('the Tx training log is at {}'.format(DEFAULT.ser_tx_train_log_dir))
        os.chdir(DEFAULT.ser_tx_train_log_dir)
        for tx_file in glob.glob('*.*.*.*'):  # training must be done with one TX
            f = open(tx_file, 'r')
            while True:
                line1 = f.readline()
                line2 = f.readline()
                _     = f.readline()
                if not line2:
                    break
                txlog = TxLog(line1, line2)
                self.tx_transmit_log[(txlog.x, txlog.y)].append(txlog)
            f.close()
        os.chdir(cwd)


    def init_train_power(self):
        '''extract the Tx transmitting power during training
        '''
        cwd = os.getcwd()
        os.chdir(DEFAULT.ser_tx_train_log_dir)
        for tx_file in glob.glob('*.*.*.*'):  # should be only one Tx
            f = open(tx_file, 'r')
            lines = f.readlines()
            line = lines[-2].split('|')
            name = line[0].split(' ')[0]
            power = float(line[3].strip())
            self.train_power = {name:power}
            break
        os.chdir(cwd)


    def init_ip_2_hostname(self):
        '''IP address to hostname
        '''
        print('ip 2 host files are at {}'.format(DEFAULT.ser_rx_ip_host_file))
        with open(DEFAULT.ser_rx_ip_host_file, 'r') as f:
            for line in f:
                line = line.split(':')
                self.ip_2_hostname[line[0]] = line[1].strip()
        # for tx_ip_host in glob.glob(DEFAULT.ser_tx_ip_host_file + '.*'):
        #     with open(tx_ip_host, 'r') as f:
        #         for line in f:
        #             line = line.split(':')
        #             self.ip_2_hostname[line[0]] = line[1].strip()


    def train(self):
        '''First read all the Rx data
           Iterate over self.tx_transmit_log.
           For each location, initialize the hypothesis file:
           collect the data from Rx, and calculate the mean and standard deviation
        '''

        # read all Rx data, a dict of {hostname --> [ (datetime, RSS) ]}
        rx_data = defaultdict(list)
        cwd = os.getcwd()
        print('the Rx training data is at {}'.format(DEFAULT.ser_rx_train_data_dir))
        os.chdir(DEFAULT.ser_rx_train_data_dir)
        for rx_ip in glob.glob('*.*.*.*'):
            hostname = self.ip_2_hostname[rx_ip]
            with open(rx_ip, 'r') as f:
                for line in f:
                    line = line.split(',')
                    dt = datetime.datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                    rss = float(line[1].strip())
                    rx_data[hostname].append((dt, rss))
        os.chdir(cwd)

        for loc, logs in sorted(self.tx_transmit_log.items(), key=lambda x: x):  # key is location, val is a list of TxLog
            x, y = loc
            x, y = int(x), int(y)
            print(x, y)
            hypothesis = Hypothesis(x, y)
            for txlog in logs:  # at one location, Tx might has multiple activities
                start = txlog.start
                end   = txlog.end
                for hostname, rss_list in sorted(rx_data.items()):    # rss_list -- [tuple<datatime, float>], a large list of all hypothesis sorted by datatime
                    index_start = bisect_right(rss_list, (start, 0))  # binary search, the data is sorted by datetime
                    index_end   = bisect_left(rss_list, (end, 0))
                    for i in range(index_start, index_end):
                        hypothesis.data[hostname].append(rss_list[i][1])
            if len(hypothesis.data) != len(hypothesis.sensors):
                print('some sensor has zero RSS data at hypothesis ({}, {})!'.format(x, y))
            for hostname, rss_list in hypothesis.data.items():        # rss_list -- [float], a small list of one hypothesis
                mean = np.mean(rss_list)
                std  = np.std(rss_list)
                sen_index = hypothesis.sensors[hostname].index
                if len(rss_list) != 30:
                    sen_x, sen_y = hypothesis.sensors[hostname].x, hypothesis.sensors[hostname].y
                    print('tx = ({}, {}), rx = ({}, {}), data size = {}'.format(x, y, sen_x, sen_y, len(rss_list)))
                hypothesis.means[sen_index] = mean
                hypothesis.stds[sen_index]  = std
            self.hypotheses[(x, y)] = hypothesis
        print('Training stage done!')


    def save_as_localization_input(self, directory=None):
        '''Save the hypothesis data into three files that the localization module can utilize: 1) cov 2) sensors 3) hypothesis
           Note that the location here is discretized, i.e. locations are integers
        '''
        if directory is None:
            directory = DEFAULT.ser_training

        # 1. covariance matrix. this assumes that a sensor's std is the same across the hypotheses. i.e. one sensor one std
        sensor_std = []
        for _, hypo in self.hypotheses.items():
            sensor_std.append(hypo.stds)
        global_stds = np.mean(sensor_std, axis=0)  # the stds are well indexed
        sen_num = len(global_stds)
        with open(directory + '/cov', 'w') as f:
            cov = np.zeros((sen_num, sen_num))
            for i in range(sen_num):
                for j in range(sen_num):
                    if i == j:
                        cov[i, j] = global_stds[i] ** 2
                    f.write('{} '.format(cov[i, j]))
                f.write('\n')

        # 2. sensors
        with open(directory + '/sensors', 'w') as f:
            one_hypo = list(self.hypotheses.values())[0]     # every hypo in self.hypotheses has the same sensors member, so pick the first one
            host_sensors  = sorted(one_hypo.sensors.items(), key=lambda t: t[1].index) # sort by index of sensor
            for host_sensor, std in zip(host_sensors, global_stds):
                sensor = host_sensor[1]
                f.write('{} {} {} {}\n'.format(int(sensor.x), int(sensor.y), std, 1))  # uniform cost

        # 3. hypothesis
        with open(directory + '/hypothesis', 'w') as f:
            for _, hypo in sorted(self.hypotheses.items()):
                t_x = hypo.x_int
                t_y = hypo.y_int
                for host_sensor in sorted(hypo.sensors.items(), key=lambda t: t[1].index): # sort by index of sensor
                    sensor = host_sensor[1]
                    s_x   = int(sensor.x)
                    s_y   = int(sensor.y)
                    index = sensor.index
                    mean  = hypo.means[index]
                    std   = hypo.stds[index]
                    # std   = global_stds[index]
                    f.write('{} {} {} {} {} {}\n'.format(t_x, t_y, s_x, s_y, mean, std))

        # 4. save training power
        with open(directory + '/train_power', 'w') as f:
            f.write(json.dumps(self.train_power))
        print('saved to {}!'.format(directory))


    def get_interpolation_error(self, inter_hypo, rss_log):
        '''
        '''
        # get the hypothesis data (including interpolated values)
        hypo_data = {}   # { (t_x, t_y, s_x, s_y) --> rss }
        with open(inter_hypo + '/hypotheses', 'r') as f:
            for line in f:
                line = line.split(' ')
                try:
                    t_x = int(line[0])
                    t_y = int(line[1])
                    s_x = int(line[2])
                    s_y = int(line[3])
                    rss = float(line[4])
                    hypo_data[(t_x, t_y, s_x, s_y)] = rss
                except Exception as e:
                    print(e)

        # the ground truth read the data from rss_log
        rx_data = defaultdict(list)     # {loc --> [ (datetime, rss) ]}
        with open(rss_log, 'r') as f:
            for line in f:
                line = line.split(',')
                dt = datetime.datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                rss = float(line[1].strip())
                x, y = line[2].strip().split(' ')
                x, y = int(float(x)), int(float(y))
                rx_data[(x, y)].append((dt, rss))

        errors = []
        for loc, logs in sorted(self.tx_transmit_log.items(), key=lambda x: x):
            t_x, t_y = int(loc[0]), int(loc[1])
            for txlog in logs:
                start = txlog.start
                end   = txlog.end
                for sen_loc, rss_list in sorted(rx_data.items()):
                    s_x, s_y = sen_loc
                    index_start = bisect_right(rss_list, (start, 0))
                    index_end   = bisect_left(rss_list, (end, 0))
                    truth_rss = []
                    for i in range(index_start, index_end):
                        truth_rss.append(rss_list[i][1])
                    truth_mean = np.mean(truth_rss)
                    inter_mean = hypo_data[t_x, t_y, s_x, s_y]
                    errors.append(abs(inter_mean - truth_mean))
        print(errors)
        print(np.mean(errors))

    @staticmethod
    def prepare_training_data(num_samples):
        '''collect rx data and tx log. first remove the existing rx and tx data, then collect the data from rx and tx
        Args:
            num_samples (int): number of samples
        '''
        for rx_file in glob.glob(DEFAULT.ser_rx_data_dir + '/*.*.*.*'):
            os.remove(rx_file)
        for tx_file in glob.glob(DEFAULT.ser_tx_log_dir + '/*.*.*.*'):
            os.remove(tx_file)
        CollectRx.get_rss_data(num_samples)
        CollectTx.get_tx_log(['wings'], mode='train')



class TxLog:
    '''One TxLog instance encapsulates the activity of one transmitter at one location (hypothesis)
    '''
    def __init__(self, line1, line2):
        self.name = ''
        self.start = None
        self.end   = None
        self.x     = -1
        self.y     = -1
        self.gain  = -1

        line1 = line1.split('|')
        line2 = line2.split('|')
        self.name = line1[0].split(' ')[0]
        self.start = datetime.datetime.strptime(line1[1].strip(), '%Y-%m-%d %H:%M:%S')
        self.end   = datetime.datetime.strptime(line2[1].strip(), '%Y-%m-%d %H:%M:%S')
        self.x, self.y = Utility.extract_location(line2[2].strip())
        self.gain = float(line1[3].strip())

    def __str__(self):
        return '({}, {}), {}, start={}, end={}, gain={}'.format(self.x, self.y, self.name, self.start, self.end, self.gain)


class Hypothesis:
    '''Encapsulate a hypothesis, which is essentially a location for a transmitter
    '''

    def __init__(self, x, y):
        '''
        Args:
            x (float)
            y (float)
        '''
        self.x_real = x               # (x, y) is the 2D index for a hypothesis
        self.y_real = y
        self.x_int  = int(x)
        self.y_int  = int(y)
        self.hypo_index = self.x_int * Train.MAP.y_axis_len + self.y_int
        self.sensors = {}             # {hostname --> Sensor}
        self.init_sensors()
        self.data = defaultdict(list) # {hostname --> []}, the data collected at this hypothesis
        self.means = np.zeros(len(self.sensors))
        self.stds  = np.zeros(len(self.sensors))


    def init_sensors(self):
        with open(DEFAULT.ser_rx_loc_file, 'r') as f:
            counter = 0
            for line in f:
                line = line.replace(' ', '')
                line = line.split(':')
                hostname = line[0]
                loc = line[1].strip()
                x, y = Utility.extract_location(loc)
                s = Sensor(x, y, index=counter, hostname=hostname)  # here x, y are float, but the input for localization is int
                self.sensors[hostname] = s
                counter += 1


    def resize_mean_std(self, size):
        '''enlarge self.means and self.stds, to make room for the new sensors
        '''
        self.means.resize(size)
        self.stds.resize(size)


    def add_inter_sensor(self, x, y, mean, std, index):
        '''Add an interpolated sensor
        Args:
            x -- float
            y -- float
            mean -- float
            std  -- float
            index -- int
        '''
        sensor = Sensor(x, y, std=std, index=index, interpolate=True)
        hostname = 'inter({},{})'.format(int(x), int(y))
        self.sensors[hostname] = sensor
        self.means[index] = mean
        self.stds[index] = std



if __name__ == '__main__':

    hint = 'Hint: python train.py | ' + \
                 'python train.py -inter idw | ' + \
                 'python train.py -ierr training/8.31-inter rx_data/rss_acer'

    parser = argparse.ArgumentParser(description = 'Training and interpolation. ' + hint)
    parser.add_argument('-inter', '--interpolation', type = str, nargs = 1, default = [''], help='interpolation method')
    parser.add_argument('-ierr',  '--inter_error', type = str, nargs = 2, default=['', ''], help = 'the hypothesis file (include intrepolated values), the ground truth')
    parser.add_argument('-mydir', '--directory', type=str, nargs=1, default=[''], help='the directory to save the training data and localization input')
    parser.add_argument('-src', '--data_source', type=str, nargs=1, default=['testbed-indoor'], help='data source: testbed-indoor, testbed-outdoor')
    args = parser.parse_args()

    interpolation = args.interpolation[0]
    inter_file, truth_file = args.inter_error
    mydir = args.directory[0]
    data_source = args.data_source[0]

    if mydir == '':
        raise ValueError('has to be a directory')
    if data_source == 'testbed-indoor':
        Train.MAP = IndoorMap
    elif data_source == 'testbed-outdoor':
        Train.MAP = OutdoorMap
    else:
        raise Exception('data source {} invalide'.format(data_source))

    data_prepared = raw_input('is data prepared? (y/n): ')
    if data_prepared == 'n':
        num_samples = raw_input('Please input the number of samples: ')
        Train.prepare_training_data(int(num_samples))

    t = Train()

    if inter_file is not '' and truth_file is not '':
        t.get_interpolation_error(inter_file, truth_file)
    else:
        t.train()
        raw_input('if needed, remember to manually delete duplicate rows with 0 mean, 0 std and manually impute them, then run plot.py again.')
        if interpolation == 'idw':
            t_inter = Interpolate.idw_baseline(t)
        elif interpolation == 'idw+':
            t_inter = Interpolate.idw_improve(t)
        t.save_as_localization_input()

    # organize the directories and files
    if os.path.exists(DEFAULT.ser_rx_data_dir + '/' + mydir) is False:
        os.mkdir(DEFAULT.ser_rx_data_dir + '/' + mydir)
    if os.path.exists(DEFAULT.ser_tx_log_dir + '/' + mydir) is False:
        os.mkdir(DEFAULT.ser_tx_log_dir + '/' + mydir)
    if os.path.exists(DEFAULT.ser_training + '/' + mydir) is False:
        os.mkdir(DEFAULT.ser_training + '/' + mydir)

    cwd = os.getcwd()
    shutil.copy(cwd + '/' + DEFAULT.ser_rx_ip_host_file, cwd + '/' + DEFAULT.ser_rx_data_dir + '/' + mydir) # copy ip_2_hostname

    os.chdir(DEFAULT.ser_rx_data_dir)
    hostname_loc = DEFAULT.ser_rx_loc_file.split('/')[1].strip()
    shutil.copy(hostname_loc, cwd + '/' + DEFAULT.ser_training + '/' + mydir + '/' + hostname_loc) # for localization input.
    shutil.copy(hostname_loc,  cwd + '/' + DEFAULT.ser_rx_data_dir + '/' + mydir + '/' + hostname_loc)
    for f in glob.glob('*.*.*.*'):
        shutil.copy(f, cwd + '/' + DEFAULT.ser_rx_data_dir + '/' + mydir) # copy the data of the sensors
    os.chdir(cwd)

    os.chdir(DEFAULT.ser_tx_log_dir)
    for f in glob.glob('*.*.*.*'):
        shutil.copy(f, cwd + '/'  + DEFAULT.ser_tx_log_dir + '/' + mydir) # copy the log of Tx
    os.chdir(cwd)

    os.chdir(DEFAULT.ser_training)
    shutil.copy('cov', cwd  + '/' + DEFAULT.ser_training + '/' + mydir)
    shutil.copy('hypothesis', cwd  + '/' + DEFAULT.ser_training + '/' + mydir)
    shutil.copy('sensors', cwd  + '/' + DEFAULT.ser_training + '/' + mydir)
    shutil.copy('train_power', cwd + '/' + DEFAULT.ser_training + '/' + mydir)
    os.remove('cov')
    os.remove('hypothesis')
    os.remove('sensors')
    os.remove('train_power')
    os.chdir(cwd)

    # plot the trained data
    command = "python plot.py -mydir {} -src {}".format(mydir, data_source)
    p = Popen(command, shell=True)
    p.wait()
