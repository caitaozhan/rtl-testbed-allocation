'''
Interpolate the training data, which is incomplete
'''

import math
import datetime
import matplotlib.pyplot as plt
import numpy as np
from subprocess import Popen
from collections import defaultdict
from utility import Utility
from default_config import DEFAULT


class Interpolate:

    same_grid_rss = -10   # the RSS value for distance around half grid-cell length
    same_grid_std = 3
    zero_prior    = []    # not to interpolate
    neighbor_num  = 3
    neighbor_dist = 4
    idw_exponent  = 2

    @staticmethod
    def idw_baseline(train):
        '''
        Args:
            train -- Train
        Return:
            Train
        '''
        print('Interpolating ...')
        # step 1: find the RSS when Tx and Rx are at the same location
        rss_same = []
        sensors = train.hypotheses.values()[0].sensors
        for _, sensor in sensors.items(): # key is hostname
            sen_x, sen_y = float(int(sensor.x)), float(int(sensor.y))
            sen_index = sensor.index
            hypo = train.hypotheses[(sen_x, sen_y)]
            rss = hypo.means[sen_index]
            rss_same.append(rss)
        rss_same.remove(max(rss_same))
        rss_same.remove(min(rss_same))
        Interpolate.same_grid_rss = np.mean(rss_same)

        # step 1: give the interpolated sensors an index
        hypothesis = list(train.hypotheses.values())[0]
        sensor_index_grid = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len), dtype=int)
        sensor_index_grid.fill(-1)
        counter = len(hypothesis.sensors)
        for _, sensor in sorted(hypothesis.sensors.items(), key=lambda x:x[1].index):
            sensor_index_grid[int(sensor.x)][int(sensor.y)] = sensor.index
        for x in range(sensor_index_grid.shape[0]):
            for y in range(sensor_index_grid.shape[1]):
                if sensor_index_grid[x][y] == -1:
                    sensor_index_grid[x][y] = counter
                    counter += 1

        # step 2: the interpolation
        for loc, hypothesis in sorted(train.hypotheses.items()):
            # construct a grid for one transmitter (hypothesis)
            t_x, t_y = int(loc[0]), int(loc[1])
            grid_rss = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len))
            grid_std = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len))

            for zero in Interpolate.zero_prior:
                grid_rss[zero[0]][zero[1]] = np.nan
                grid_std[zero[0]][zero[1]] = np.nan
            for _, sensor in sorted(hypothesis.sensors.items(), key=lambda x:x[1].index):
                grid_rss[int(sensor.x)][int(sensor.y)] = hypothesis.means[sensor.index]  # true data
                grid_std[int(sensor.x)][int(sensor.y)] = hypothesis.stds[sensor.index]

            hypothesis.resize_mean_std(train.MAP.x_axis_len * train.MAP.y_axis_len)
            if grid_rss[t_x][t_y] == 0:
                grid_rss[t_x][t_y] = Interpolate.same_grid_rss
                grid_std[t_x][t_y] = Interpolate.same_grid_std  # for locations at the Tx itself, do not use neighbor averaging.
                hypothesis.add_inter_sensor(t_x + 0.5, t_y + 0.5, Interpolate.same_grid_rss, Interpolate.same_grid_std, sensor_index_grid[t_x][t_y])

            # find the zero elements and impute them
            for x in range(grid_rss.shape[0]):
                for y in range(grid_rss.shape[1]):
                    if grid_rss[x][y] != 0.0:
                        continue
                    points = []
                    d = Interpolate.neighbor_dist
                    for i in range(x - d, x + d + 1):
                        for j in range(y - d, y + d + 1):
                            if i < 0 or i >= grid_rss.shape[0] or j < 0 or j >= grid_rss.shape[1]:
                                continue
                            dist = Utility.distance((x, y), (i, j))
                            if grid_rss[i][j] == 0.0 or np.isnan(grid_rss[i][j]) or dist > Interpolate.neighbor_dist:
                                continue
                            points.append( (i, j, dist) )
                    points = sorted(points, key=lambda tup: tup[2])
                    threshold = min(Interpolate.neighbor_num, len(points))
                    weights = np.zeros(threshold)
                    for i in range(threshold):
                        dist = points[i][2]
                        weights[i] = (1./dist)**Interpolate.idw_exponent
                    weights /= np.sum(weights)
                    idw_rss = 0
                    idw_std = 0
                    for i in range(threshold):
                        w = weights[i]
                        rss = grid_rss[points[i][0]][points[i][1]]
                        std = grid_std[points[i][0]][points[i][1]]
                        idw_rss += w * rss
                        idw_std += w * std
                    hypothesis.add_inter_sensor(x+0.5, y+0.5, idw_rss, idw_std, sensor_index_grid[x][y])
            train.hypotheses[loc] = hypothesis
        return train


    @staticmethod
    def idw_improve(train):
        '''The higher level idea is to utilize the information that power is linear to log10 distance
        Args:
            train -- Train
        Return:
            Train
        '''
        print('Interpolating ...')
        # step 1: find the RSS when Tx and Rx are at the same location
        rss_same = []
        sensors = train.hypotheses.values()[0].sensors
        for _, sensor in sensors.items(): # key is hostname
            sen_x, sen_y = float(int(sensor.x)), float(int(sensor.y))
            sen_index = sensor.index
            hypo = train.hypotheses[(sen_x, sen_y)]
            rss = hypo.means[sen_index]
            rss_same.append(rss)
        rss_same.remove(max(rss_same))
        rss_same.remove(min(rss_same))
        Interpolate.same_grid_rss = np.mean(rss_same)

        # step 1: give the interpolated sensors an index
        hypothesis = list(train.hypotheses.values())[0]
        sensor_index_grid = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len), dtype=int)
        sensor_index_grid.fill(-1)
        counter = len(hypothesis.sensors)
        for _, sensor in sorted(hypothesis.sensors.items(), key=lambda x:x[1].index):
            sensor_index_grid[int(sensor.x)][int(sensor.y)] = sensor.index
        for x in range(sensor_index_grid.shape[0]):
            for y in range(sensor_index_grid.shape[1]):
                if sensor_index_grid[x][y] == -1:
                    sensor_index_grid[x][y] = counter
                    counter += 1

        # step 2: the interpolation
        for loc, hypothesis in sorted(train.hypotheses.items()):
            # construct a grid for one transmitter (hypothesis)
            t_x, t_y = int(loc[0]), int(loc[1])
            grid_rss = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len))
            grid_std = np.zeros((train.MAP.x_axis_len, train.MAP.y_axis_len))

            for zero in Interpolate.zero_prior:
                grid_rss[zero[0]][zero[1]] = np.nan
                grid_std[zero[0]][zero[1]] = np.nan
            for _, sensor in sorted(hypothesis.sensors.items(), key=lambda x:x[1].index):
                grid_rss[int(sensor.x)][int(sensor.y)] = hypothesis.means[sensor.index]  # true data
                grid_std[int(sensor.x)][int(sensor.y)] = hypothesis.stds[sensor.index]

            hypothesis.resize_mean_std(train.MAP.x_axis_len * train.MAP.y_axis_len)
            if grid_rss[t_x][t_y] == 0:
                grid_rss[t_x][t_y] = Interpolate.same_grid_rss
                grid_std[t_x][t_y] = Interpolate.same_grid_std  # for locations at the Tx itself, do not use neighbor averaging.
                hypothesis.add_inter_sensor(t_x + 0.5, t_y + 0.5, Interpolate.same_grid_rss, Interpolate.same_grid_std, sensor_index_grid[t_x][t_y])

            # find the zero elements and impute them
            for x in range(grid_rss.shape[0]):
                for y in range(grid_rss.shape[1]):
                    if grid_rss[x][y] != 0.0:
                        continue
                    points = []
                    d = Interpolate.neighbor_dist
                    for i in range(x - d, x + d + 1):
                        for j in range(y - d, y + d + 1):
                            if i < 0 or i >= grid_rss.shape[0] or j < 0 or j >= grid_rss.shape[1]:
                                continue
                            dist = Utility.distance((x, y), (i, j))
                            if grid_rss[i][j] == 0.0 or np.isnan(grid_rss[i][j]) or dist > Interpolate.neighbor_dist:
                                continue
                            points.append( (i, j, dist) )
                    points = sorted(points, key=lambda tup: tup[2])
                    threshold = min(Interpolate.neighbor_num, len(points))
                    weights1 = np.zeros(threshold)   # inverse distance weight
                    dist_to_tx = np.zeros(threshold)  # log10 inspired weight
                    for i in range(threshold):
                        dist = points[i][2]
                        weights1[i] = (1./dist)**Interpolate.idw_exponent
                        tx = (t_x, t_y) # transmitter
                        nei = (points[i][0], points[i][1])
                        dist_to_tx[i] = Utility.distance(tx, nei)
                    weights1 /= np.sum(weights1)
                    rx0 = (x, y)
                    weights2 = Interpolate.get_log10_weight(dist_to_tx, tx, rx0)
                    weights2 /= np.sum(weights2)
                    weights = weights2
                    idw_rss = 0
                    idw_std = 0
                    for i in range(threshold):
                        w = weights[i]
                        rss = grid_rss[points[i][0]][points[i][1]]
                        std = grid_std[points[i][0]][points[i][1]]
                        idw_rss += w * rss
                        idw_std += w * std
                    hypothesis.add_inter_sensor(x+0.5, y+0.5, idw_rss, idw_std, sensor_index_grid[x][y])
            train.hypotheses[loc] = hypothesis
        return train


    @staticmethod
    def get_log10_weight(to_tx_dists, tx, rx0):
        '''get the weights from project_dists
        Args:
            project_dists  -- np.1darray
            tx -- (float, float)
            rx0 -- (float, float)  -- location to be interpolated
        Return:
            np.1darray
        '''
        for i, dist in enumerate(to_tx_dists):
            if dist == 0:
                to_tx_dists[i] = 0.25  # this value can tweak
        log10_dist_to_tx = np.log10(to_tx_dists)
        reference_dist = np.log10(Utility.distance(tx, rx0))
        log10_dist_to_rx0 = log10_dist_to_tx - reference_dist
        log10_dist_to_rx0 = np.absolute(log10_dist_to_rx0)
        weight = np.zeros(len(log10_dist_to_rx0))
        for i, dist in enumerate(log10_dist_to_rx0):
            if dist > 0:
                weight[i] = (1./dist)
        maxx = max(weight)
        for i, w in enumerate(weight):
            if w == 0:
                weight[i] = 2*maxx if maxx > 0 else 1
        return weight


    @staticmethod
    def get_interpolation_error(hypothesis_true, hypothesis_inter, dist=2):
        '''Compute the interpolation error
        Args:
            hypothesis_true  -- str -- filename
            hypothesis_inter -- str -- filename
            dist -- float -- only consider dist(tx, rx) <= dist
        Return:
            float
        '''
        hypo_data_true = {}   # { (t_x, t_y, s_x, s_y) --> rss }
        with open(hypothesis_true + '/hypothesis', 'r') as f:
            for line in f:
                line = line.split(' ')
                try:
                    t_x = int(line[0])
                    t_y = int(line[1])
                    s_x = int(line[2])
                    s_y = int(line[3])
                    rss = float(line[4])
                    hypo_data_true[(t_x, t_y, s_x, s_y)] = rss
                except Exception as e:
                    print(e)

        hypo_data_inter = {}   # { (t_x, t_y, s_x, s_y) --> rss }
        with open(hypothesis_inter + '/hypothesis', 'r') as f:
            for line in f:
                line = line.split(' ')
                try:
                    t_x = int(line[0])
                    t_y = int(line[1])
                    s_x = int(line[2])
                    s_y = int(line[3])
                    rss = float(line[4])
                    hypo_data_inter[(t_x, t_y, s_x, s_y)] = rss
                except Exception as e:
                    print(e)

        errors = []
        for tx_rx, rss_true in sorted(hypo_data_true.items()):
            tx = (tx_rx[0], tx_rx[1])
            rx = (tx_rx[2], tx_rx[3])
            if Utility.distance(tx, rx) <= dist:
                rss_inter = hypo_data_inter[tx_rx]
                error = rss_inter - rss_true
                errors.append(error)
        print('average error = {}, average abs error = {}, std = {}'.format(np.mean(errors), np.mean(np.absolute(errors)), np.std(errors)))
        plt.hist(errors, bins=20)
        plt.show()


def main1():
    '''get interpolation error
    '''

    command = 'python train.py -mydir 9.26.inter-2 -inter idw+'
    print(command)
    p = Popen(command, shell=True)
    p.wait()

    command = 'python subsample_interpolate.py -src testbed-indoor -full 9.26.inter-2 -sub 9.26.inter-sub-2'
    print(command)
    p = Popen(command, shell=True)
    p.wait()

    hypothesis_true  = 'training/9.27'
    hypothesis_inter = 'training/9.26.inter-sub-2'
    Interpolate.get_interpolation_error(hypothesis_true, hypothesis_inter)



if __name__ == '__main__':

    main1()
