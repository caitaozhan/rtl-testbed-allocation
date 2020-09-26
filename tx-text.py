#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Tx Text
# Generated: Fri Jun 26 16:26:45 2020
##################################################

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import sip
import sys
import time
import argparse
import json
import os
from default_config import DEFAULT
from utility import Utility

class tx_text(gr.top_block):

    def __init__(self, gain, freq):
        gr.top_block.__init__(self, "Tx Text")
        
        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1e6
        self.gain = gain
        self.freq = freq

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
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(freq, 0)
        self.uhd_usrp_sink_0.set_gain(gain, 0)
        self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)

        self.digital_qam_mod_0 = digital.qam.qam_mod(
          constellation_points=4,
          mod_code="gray",
          differential=True,
          samples_per_symbol=2,
          excess_bw=0.35,
          verbose=False,
          log=False,
          )
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, '/home/caitao/Project/rtl-testbed-allocation/file_transmit', True)
        self.blks2_packet_encoder_0 = grc_blks2.packet_mod_b(grc_blks2.packet_encoder(
        		samples_per_symbol=2,
        		bits_per_symbol=2,
        		preamble='',
        		access_code='',
        		pad_for_usrp=True,
        	),
        	payload_length=0,
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blks2_packet_encoder_0, 0), (self.digital_qam_mod_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.blks2_packet_encoder_0, 0))
        self.connect((self.digital_qam_mod_0, 0), (self.uhd_usrp_sink_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_sink_0.set_gain(self.gain, 0)


    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_sink_0.set_center_freq(self.freq, 0)


def main(gain, freq, top_block_cls=tx_text, options=None):

    try:
        tb = top_block_cls(gain, freq)
        tb.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = 'Passing gain and location')
    parser.add_argument('-g', '--gain', type = int, nargs = 1, default = [24], help = 'the gain of the PU TX')
    parser.add_argument('-f', '--freq', type = int, nargs = 1, default = [DEFAULT.tx_freq], help = 'the frequency of the PU TX')
    parser.add_argument('-x', '--x_coord', type = float, nargs = 1, default = [-1], help = 'the x coordinate of the transmitter')
    parser.add_argument('-y', '--y_coord', type = float, nargs = 1, default = [-1], help = 'the y coordinate of the transmitter')
    parser.add_argument('-o', '--off', action='store_true', help='this argument means turn the TX off (TX not running)')
    
    args = parser.parse_args()
    gain = args.gain[0]
    freq = args.freq[0]
    x = args.x_coord[0]
    y = args.y_coord[0]
    off = args.off

    Utility.guarantee_dir(DEFAULT.pu_info_dir)
    with open(DEFAULT.file_transmit, 'w') as f:
        f.write('hello world\n')

    if off:
        with open(DEFAULT.pu_info_file, 'w') as f:
            hostname = os.uname()[1]
            pu_info = {'hostname':hostname, 'gain':gain, 'freq':freq, 'x':x, 'y':y, 'tx_on':'False'}
            json.dump(pu_info, f)
    else:
        with open(DEFAULT.pu_info_file, 'w') as f:
            hostname = os.uname()[1]
            pu_info = {'hostname':hostname, 'gain':gain, 'freq':freq, 'x':x, 'y':y, 'tx_on':'True'}
            json.dump(pu_info, f)
        main(gain, freq)
