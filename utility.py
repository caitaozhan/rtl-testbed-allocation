'''
Utlities
'''

import os
import math
from subprocess import Popen, PIPE
from mpu import haversine_distance


class Utility:

    @staticmethod
    def extract_location(loc_str):
        '''
        Args:
            loc_str -- str: eg. (1.0, 2.0)
        Return:
            (float, float)
        '''
        loc_str = loc_str.replace(' ', '')
        loc_str = loc_str.replace('(', '')
        loc_str = loc_str.replace(')', '')
        x, y = loc_str.split(',')
        return float(x), float(y)

    @staticmethod
    def distance(point1, point2):
        '''
        Args:
            point1 -- (float, float)
            point2 -- (float, float)
        Return:
            float
        '''
        return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

    @staticmethod
    def gps_2_coordinate(gps, outdoormap):
        '''Get the coordinate according to the origin
        Args:
            gps -- tuple<float, float>
        return:
            tuple<float, float> -- the (x, y) cooridinate
        '''
        a, b = gps
        lat_origin = outdoormap.origin[0]
        lon_origin = outdoormap.origin[1]
        y = haversine_distance((lat_origin, b), (a, b)) * 1000  # from km to m
        x = haversine_distance((a, lon_origin), (a, b)) * 1000
        y_sign = 1 if a > lat_origin else -1
        x_sign = 1 if b > lon_origin else -1
        try:
            return x_sign * x / outdoormap.cell_len, y_sign * y / outdoormap.cell_len
        except Exception as e:
            print(e)
            return -1, -1

    @staticmethod
    def guarantee_dir(directory):
        '''Gurantee that a directory exists
        Args:
            directory -- str
        '''
        if os.path.exists(directory) is False:
            os.mkdir(directory)


    @staticmethod
    def program_is_running(program):
        '''if tx_text.py is running the command will return a list of three elements
            ['caitao   23206 14243 99 20:26 pts/0    00:00:14 /usr/bin/python -u /home/caitao/Project/rtl-testbed-allocation/tx_text.py\n', 
            'caitao   23283 23280  0 20:26 pts/4    00:00:00 /bin/sh -c ps -ef | grep tx_text.py\n', 
            'caitao   23285 23283  0 20:26 pts/4    00:00:00 grep tx_text.py\n']
        '''
        command = 'ps -ef | grep {}'.format(program)
        p = Popen(command, shell=True, stdout=PIPE)
        p.wait()
        stdout = p.stdout.readlines()
        if len(stdout) >= 3:
            return True
        else:
            return False


if __name__ == '__main__':
    print(Utility.program_is_running('tx_text.py'))
