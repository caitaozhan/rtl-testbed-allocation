'''Plotting
'''

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from default_config import IndoorMap, OutdoorMap


class Data:
    training_dir = 'training/{}'


class Plot:

    @staticmethod
    def visualize_training(training_dir, MAP):
        hypo_data = defaultdict(list)
        with open(training_dir + '/hypothesis', 'r') as f:
            for line in f:
                line = line.split(' ')
                try:
                    t_x = int(line[0])
                    t_y = int(line[1])
                    s_x = int(line[2])
                    s_y = int(line[3])
                    rss = float(line[4])
                    std = float(line[5])
                    hypo_data[(t_x, t_y)].append((s_x, s_y, rss, std))
                except Exception as e:
                    print(e)
        if os.path.exists(training_dir + '/visualize') is not True:
            os.mkdir(training_dir + '/visualize')
        for tx, s_list in sorted(hypo_data.items()):
            grid = np.zeros((MAP.x_axis_len, MAP.y_axis_len))
            t_x, t_y = tx
            grid[t_x][t_y] = 1
            for s_x, s_y, rss, _ in s_list:
                grid[s_x][s_y] = rss

            grid2 = np.zeros((MAP.y_axis_len, MAP.x_axis_len))
            for i in range(MAP.y_axis_len):
                for j in range(MAP.x_axis_len):
                    grid2[i][j] = grid[j][MAP.y_axis_len - 1 - i]

            plt.subplots(figsize=(10, 6))
            sns.heatmap(grid2, vmin=np.min(grid), vmax=np.max(grid), square=True, linewidth=0.5, annot=True)
            plt.title('{}. Transmitter at ({}, {}). Mean.'.format(IndoorMap.name, t_x, t_y))
            plt.savefig(training_dir + '/visualize/({}, {})-mean'.format(t_x, t_y))

        for tx, s_list in sorted(hypo_data.items()):
            grid = np.zeros((MAP.x_axis_len, MAP.y_axis_len))
            t_x, t_y = tx
            grid[t_x][t_y] = 1
            for s_x, s_y, _, std in s_list:
                grid[s_x][s_y] = std

            grid2 = np.zeros((MAP.y_axis_len, MAP.x_axis_len))
            for i in range(MAP.y_axis_len):
                for j in range(MAP.x_axis_len):
                    grid2[i][j] = grid[j][MAP.y_axis_len - 1 - i]

            plt.subplots(figsize=(10, 6))
            sns.heatmap(grid2, vmin=np.min(grid), vmax=np.max(grid), square=True, linewidth=0.5, annot=True)
            plt.title('{}. Transmitter at ({}, {}). Std.'.format(IndoorMap.name, t_x, t_y))
            plt.savefig(training_dir + '/visualize/({}, {})-std'.format(t_x, t_y))
        print('Plots generated in {}'.format(training_dir + '/visualize'))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'plot the trained data')
    parser.add_argument('-mydir', '--directory', type=str, nargs=1, default=[''], help='the directory to save the training data and localization input')
    parser.add_argument('-src', '--data_source', type=str, nargs=1, default=['indoor'], help='indoor or outdoor testbed environment')
    args = parser.parse_args()

    mydir = args.directory[0]
    data_source = args.data_source[0]

    if mydir == '':
        raise ValueError('there is no directory')
    if data_source == 'testbed-indoor':
        mymap = IndoorMap
    elif data_source == 'testbed-outdoor':
        mymap = OutdoorMap
    else:
        raise ValueError('invalid data source! {}'.format(data_source))

    Data.training_dir = Data.training_dir.format(mydir)
    if os.path.exists(Data.training_dir) is False:
        os.mkdir(Data.training_dir)

    training_dir = Data.training_dir

    Plot.visualize_training(training_dir, mymap)
