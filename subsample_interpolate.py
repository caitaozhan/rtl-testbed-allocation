'''
After interpolating all the places, subsample a subset of locations to place the sensors.
'''

import argparse
import pandas as pd
import shutil
import numpy as np
from subprocess import Popen
from default_config import DEFAULT
from utility import Utility



class SubsampleInterpolate:
    '''Subsample sensors from a fully interpolated data
    '''
    def __init__(self, new_hostname_loc_file, full_interpolate_dir, subsample_dir):
        self.new_hostname_loc_file = new_hostname_loc_file
        self.full_interpolate_dir  = full_interpolate_dir
        self.subsample_dir         = subsample_dir
        self.new_sensors = []   # list<tuple<int, int>>
        self.init_new_sensor()
        Utility.guarantee_dir(self.subsample_dir)
        print(self)

    def __str__(self):
        a = 'new hostname loc file = {}\nfull interpolate dir = {}\nsubsample dir = {}\n'.format(\
            self.new_hostname_loc_file, self.full_interpolate_dir, self.subsample_dir)
        b = '; '.join([str(sen) for sen in self.new_sensors])
        return a + b

    def init_new_sensor(self):
        '''New location of sensors for the interpolation
        '''
        with open(self.new_hostname_loc_file, 'r') as f:
            for line in f:
                line = line.split(':')
                loc = Utility.extract_location(line[1])
                x, y = int(loc[0]), int(loc[1])
                self.new_sensors.append((x, y))

    def save_as_localization_input(self):
        '''Read in the fully interpolated data, and only save the new sensors to a desired directory
        '''

        all_sensors = []
        # step 1: sensors. read the sensors file and get the index for sensors in self.sensor
        with open(self.full_interpolate_dir + '/sensors', 'r') as f:
            for line in f:
                line = line.split(' ')
                x, y = int(line[0]), int(line[1])
                all_sensors.append((x, y))
        new_sen_index = []
        for new_sen in self.new_sensors:
            for i, sen in enumerate(all_sensors):
                if new_sen == sen:
                    new_sen_index.append(i)
        with open(self.full_interpolate_dir + '/sensors', 'r') as full_f, open(self.subsample_dir + '/sensors', 'w') as sub_f:
            all_lines = full_f.readlines()
            for sen_index in new_sen_index:
                sub_line = all_lines[sen_index]
                sub_f.write(sub_line)

        # step 2: deal with the subsample cov
        cov = pd.read_csv(self.full_interpolate_dir + '/cov', header=None, delimiter=' ')
        cov = cov.values
        cov = cov[np.ix_(new_sen_index, new_sen_index)]
        np.savetxt(self.subsample_dir + '/cov', cov, delimiter='', fmt='%1.8f ')

        # step 3: deal with hypothesis file
        with open(self.full_interpolate_dir + '/hypothesis', 'r') as full_f, open(self.subsample_dir + '/hypothesis', 'w') as sub_f:
            lines = full_f.readlines()
            num_all_sensors = len(all_sensors)
            for i in range(num_all_sensors):
                for sen_index in new_sen_index:
                    index = i*num_all_sensors + sen_index
                    print(index, lines[index])
                    sub_f.write(lines[index])

        # step 4: copy
        shutil.copy(self.full_interpolate_dir + '/train_power', self.subsample_dir + '/train_power')
        shutil.copy(self.new_hostname_loc_file, self.subsample_dir + '/hostname_loc')



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'subsample sensors from the fully interpolated data')
    parser.add_argument('-src', '--data_source', type=str, nargs=1, default=['testbed-indoor'], help='testbed-indoor or testbed-outdoor')
    parser.add_argument('-full', '--full_interpolate_dir', type=str, nargs=1, default=['9.19.inter'], help='the directory of fully interpolated data')
    parser.add_argument('-sub', '--subsample_dir', type=str, nargs=1, default=['9.19.inter-sub'], help='the input for localization module, a subsample from the fully interpolated data')
    args = parser.parse_args()

    data_source = args.data_source[0]
    full_interpolate_dir = args.full_interpolate_dir[0]
    subsample_dir = args.subsample_dir[0]

    if data_source == 'testbed-indoor':
        new_hostname_loc_file = DEFAULT.ser_rx_data_dir + '/' + 'hostname_loc_indoorinter'
    elif data_source == 'testbed-outdoor':
        new_hostname_loc_file = DEFAULT.ser_rx_data_dir + '/' + 'hostname_loc_outdoorinter'

    full_interpolate_dir = DEFAULT.ser_training + '/' + full_interpolate_dir
    subsample_dir = DEFAULT.ser_training + '/' + subsample_dir

    subInter = SubsampleInterpolate(new_hostname_loc_file, full_interpolate_dir, subsample_dir)
    subInter.save_as_localization_input()

    # plot the interpolated data
    command = "python plot.py -mydir {} -src {}".format(args.subsample_dir[0], data_source)
    print(command)
    p = Popen(command, shell=True)
    p.wait()
