'''
The TX runs this GPS program
'''

import os
import time
import numpy as np
import psutil
from subprocess import call, Popen, PIPE, check_call
from default_config import DEFAULT, OutdoorMap, HimanMap
from utility import Utility

class GPS:

    def __init__(self):
        self.p = None
        self.cwd = os.getcwd() + '/'
        self.gpsfile = open(self.cwd + DEFAULT.tx_gps_log, 'w')


    def start(self):
        command = 'sudo cat /dev/ttyACM0 > {}'.format(self.cwd + DEFAULT.tx_gps_log_raw)
        print(command)
        self.p = Popen('exec ' + command, stdout=PIPE, shell=True)
        print('GPS starts ...')


    def end(self):
        '''
        Args:
            p (Popen()): subprocess
        '''
        try:
            parent = psutil.Process(self.p.pid)
            for child in parent.children(recursive=True):
                print 'kill process {}'.format(child.pid)
                check_call(['sudo', 'kill', '-9', str(child.pid)])
        except Exception as e:
            print(e)
        print('GPS ends ...')


    def gps_process_is_running(self):
        '''check the gps process
        '''
        if self.p is not None:
            if self.p.poll() is None:  # no return code --> still running
                return True
            else:
                return False
        return False


    def process_gps_raw(self):
        command = 'tail -n 20 {}'.format(self.cwd + DEFAULT.tx_gps_log_raw)
        p = Popen(command, stdout=PIPE, shell=True)
        p.wait()
        locations = []
        for line in p.stdout:
            gps_loc = GPS.parse_one_line(line)
            if gps_loc is not None:
                locations.append(gps_loc)
        if len(locations) != 0:
            return np.mean(locations, axis=0)
        else:
            return None


    @staticmethod
    def parse_one_line(line):
        line = line.split(',')
        if line[0] == '$GPGLL':
            lat_gps_format, lon_gps_format = line[1], line[3]
            return GPS.gpsformat_2_decimal(lat_gps_format, lon_gps_format)
        if line[0] == '$GPGGA':
            lat_gps_format, lon_gps_format = line[2], line[4]
            return GPS.gpsformat_2_decimal(lat_gps_format, lon_gps_format)
        return None


    @staticmethod
    def gpsformat_2_decimal(lat_gps_format, lon_gps_format):
        '''
        Args:
            lat_gps_format -- str -- eg. 4054.74608
            lon_gps_format -- str -- eg. 07307.35060
        Return:
            [float, float] -- the decimal format of GPS locations
        '''
        try:
            lat_DD = int(float(lat_gps_format) / 100)
            lat_MM = float(lat_gps_format) - lat_DD * 100
            lat_dec = lat_DD + lat_MM / 60

            lon_DD = int(float(lon_gps_format) / 100)
            lon_MM = float(lon_gps_format) - lon_DD * 100
            lon_dec = lon_DD + lon_MM / 60

            return [lat_dec, -lon_dec]
        except:
            raise Exception('GPS format issue, most probobably indoor weak signal')



    def write_gps_to_file(self, gps_coord):
        '''
        Args:
            [float, float]
        '''
        lt = time.localtime()
        self.gpsfile.write('{:0.7f},{:0.7f},{}-{}-{} {}:{}:{}\n'.format(gps_coord[0], gps_coord[1], lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec))   # to buffer
        self.gpsfile.flush()                                                         # to disk



if __name__ == '__main__':

    gps = GPS()
    
    gps.start()
    time.sleep(5)   # time for input password for sudo

    try:
        while True:
            time.sleep(1)
            if gps.gps_process_is_running() == False:
                raise Exception('GPS dongle disconnected')
            
            gps_decimal = gps.process_gps_raw()

            if gps_decimal is not None:   # Need to test, when there is no GPS signal
                gps_coord = Utility.gps_2_coordinate(gps_decimal, HimanMap)
                print '({:0.7f}, {:0.7f}), ({:0.7f}, {:0.7f})'.format(gps_decimal[0], gps_decimal[1], gps_coord[0], gps_coord[1])
                gps.write_gps_to_file(gps_coord)
            else:
                print('no GPS signal')
    except KeyboardInterrupt as e:
        gps.gpsfile.close()
        #gps.end()   # with keyboardinterrupt, no need to end the Popen object myself, it automatically terminates
    except Exception as e:
        print(e)
        gps.end()
