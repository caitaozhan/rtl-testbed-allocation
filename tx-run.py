#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Fri Nov 24 15:33:37 2017
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import qtgui
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import sip
import sys
import os
import time
import argparse
import datetime
import numpy as np
import threading
from subprocess import call, Popen, PIPE, check_call

from default_config import DEFAULT

class TopBlock(gr.top_block):

    def __init__(self, gain, freqency):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 64000
        self.gain = gain
        self.freqency = freqency

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(self.freqency, 0)
        self.uhd_usrp_sink_0.set_gain(self.gain, 0)
        self.uhd_usrp_sink_0.set_bandwidth(self.samp_rate, 0)  # what does this do?

        device_info = self.uhd_usrp_sink_0.get_usrp_info()
        print device_info['mboard_serial']
          
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, self.freqency, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.uhd_usrp_sink_0, 0))    


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_sink_0.set_bandwidth(self.samp_rate, 0)
        self.qtgui_sink_x_0.set_frequency_range(self.freqency, self.samp_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_sink_0.set_gain(self.gain, 0)



class TxLogger:
    '''
    '''
    def __init__(self, outputfile):
        self.cwd = os.getcwd() + '/'
        self.log_file = open(self.cwd + outputfile, 'a')
        self.start_time = None
        self.test_flag = True
    
    
    def start_transmit(self, tx_name, x, y, gps, gain):
        '''one line of log for Tx start transmitting
        '''
        lt = time.localtime()
        if gps:
            gps_x, gps_y = self.get_latest_gps_coord()
            self.log_file.write('T{} starts | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, gps_x, gps_y, gain))
        else:
            self.log_file.write('T{} starts | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, x, y, gain))
        self.log_file.flush()


    def transmitting(self, tx_name, x, y, gps, gain):
        '''one line of log (per few seconds) for Tx during transmition
        '''
        if self.log_file.closed:
            return

        lt = time.localtime()
        if gps:
            gps_x, gps_y = self.get_latest_gps_coord()
            self.log_file.write('T{}        | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, gps_x, gps_y, gain))
        else:
            self.log_file.write('T{}        | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, x, y, gain))
        self.log_file.flush()


    def end_transmit(self, tx_name, x, y, gps, gain):
        '''one line of log for Tx end transmitting
        '''
        lt = time.localtime()
        if gps:
            gps_x, gps_y = self.get_end_gps_coord()
            self.log_file.write('T{} ends   | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, gps_x, gps_y, gain))
        else:
            self.log_file.write('T{} ends   | {}-{}-{} {}:{}:{} | ({}, {}) | {}\n\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, x, y, gain))
        self.log_file.close()


    def get_latest_gps_coord(self):
        '''GPS coordinate of the latest single (x, y), and save the start_time
        '''
        tail = 'tail -n 1 {}'
        command = tail.format(DEFAULT.tx_gps_log)
        p = Popen(command, stdout=PIPE, shell=True)
        p.wait()
        line = p.stdout.readline().split(',')
        x, y = float(line[0]), float(line[1])
        dt = datetime.datetime.strptime(line[2].strip(), '%Y-%m-%d %H:%M:%S')
        self.start_time = dt
        return x, y


    def get_end_gps_coord(self):
        '''GPS coordinate of the latest multiple (x, y) since start_time, and do an average
        '''
        tail = 'tail -n 100 {}'
        command = tail.format(DEFAULT.tx_gps_log)
        p = Popen(command, stdout=PIPE, shell=True)
        p.wait()
        coords = []
        for line in p.stdout:
            line = line.split(',')
            dt = datetime.datetime.strptime(line[2].strip(), '%Y-%m-%d %H:%M:%S')
            if dt > self.start_time:
                x, y = float(line[0]), float(line[1])
                coords.append((x, y))
        print 'mean', np.mean(coords, axis=0)
        print 'std ', np.std(coords, axis=0)
        print 'min ', np.min(coords, axis=0)
        print 'max ', np.max(coords, axis=0)
        return np.mean(coords, axis=0)


    def test_log(self, tx_name, x, y, gps, gain):
        '''call self.transmitting every few seconds
        '''
        while self.test_flag:
            time.sleep(1)
            self.transmitting(tx_name, x, y, gps, gain)



if __name__ == '__main__':

    description = 'Let Tx transmit signals.' + \
                  'Hint: python tx-run.py -n 2 -hrf -g 40 | ' + \
                        'python tx-run.py -n 2 -g 100 -x 3.5 -y 4.5 | ' + \
                        'python tx-run.py -n 2 -g 100 -gps'

    parser = argparse.ArgumentParser(description = description)
    parser.add_argument('-n', '--name', type=int, nargs=1, default=[1], help='the name of the transmitter')
    parser.add_argument('-hrf', '--hackrf', action='store_true', help='Whether is hackrf of usrp, default is false')
    parser.add_argument('-g', '--gain', type = int, nargs = 1, default = [DEFAULT.tx_gain], help = 'Gain of the transmitter')
    parser.add_argument('-f', '--freq', type = int, nargs = 1, default = [DEFAULT.tx_freq], help = 'Frequency of the transmitter')
    parser.add_argument('-x', '--x_coord', type = float, nargs = 1, default = [-1], help = 'X coordinate of the transmitter')
    parser.add_argument('-y', '--y_coord', type = float, nargs = 1, default = [-1], help = 'Y coordinate of the transmitter')
    parser.add_argument('-mo', '--mode', type=str, nargs=1, default=['train'], help='output file location')
    parser.add_argument('-gps', '--gps', action='store_true', help='Tx has GPS')
    args = parser.parse_args()

    # get command line arguments
    tx_name = args.name[0]
    hackrf = args.hackrf
    gain = args.gain[0]
    freq = args.freq[0]
    x = args.x_coord[0]
    y = args.y_coord[0]
    mode = args.mode[0]
    gps = args.gps
    print 'transmitter running, gain and frequency are', (gain, freq), '\n'

    if mode == 'train':
        outputfile = DEFAULT.tx_train_log
    elif mode == 'test':                     # two modes have a different logging behavior
        outputfile = DEFAULT.tx_test_log
    else:
        raise Exception('mode = {} invalid'.format(mode))

    txlogger = TxLogger(outputfile)
    txlogger.start_transmit(tx_name, x, y, gps, gain)

    if mode == 'test':
        t = threading.Thread(target=txlogger.test_log, args=(tx_name, x, y, gps, gain,))
        t.start()

    ############## start sending signals ##################
    if hackrf:
        try:
            command = 'sudo hackrf_transfer -f {}  -x {}  -a 1 -c 60'.format(freq, gain)
            print(command)
            call(command, shell=True)
        except KeyboardInterrupt:
            pass
    else: # usrp
        try:
            tb = TopBlock(gain, freq)
            tb.run()
        except KeyboardInterrupt:
            pass

    txlogger.test_flag = False
    txlogger.end_transmit(tx_name, x, y, gps, gain)
