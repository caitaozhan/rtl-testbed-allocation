'''
This code is executed on the receiver/sensor side
Reads data from RTL-SDR and plots the live data as animation.
@author: Caitao Zhan
'''

import os
import matplotlib

if os.environ.get('DISPLAY', '') == '':
    # print('no display found. using non-interactive Agg backend')
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import math
import time
import argparse
from rtlsdr import RtlSdr
from default_config import DEFAULT



class Receiver:
    '''
    1. Read receiver's data using rtlsdr package
    2. Do FFT by plt.psd()
    3. Update an animation by calling __call__(), refer to https://matplotlib.org/3.1.1/gallery/animation/bayes_update.html
    '''
    def __init__(self, ax0, ax1, ax1_num, sample_rate, center_freq, gain, num_samp, nfft, sleep, output, x_coord, y_coord, timestamp):
        '''
        Args:
            ax (plt.axes)
        '''
        self.ax0 = ax0
        self.ax1 = ax1
        self.ax1_num = ax1_num
        self.power_peaks = []
        self.freq_peaks = []
        self.sdr = RtlSdr()
        self.sdr.sample_rate = sample_rate
        self.sdr.center_freq = center_freq
        self.sdr.gain        = gain
        self.num_sample      = num_samp
        self.NFFT            = nfft
        self.sleep           = sleep
        self.output          = output
        self.x               = x_coord
        self.y               = y_coord
        self.timestamp       = timestamp


    def sample_rss(self, sample_iteration):
        '''Sample without animation
        '''
        if os.path.exists(self.output) and os.path.getsize(self.output) > DEFAULT.rx_rss_file_max:
            os.remove(self.output)

        iteration = 0
        while iteration < sample_iteration+1 or sample_iteration == -1:
            samples = self.sdr.read_samples(self.num_sample)
            pxx, _ = plt.psd(samples, NFFT=self.NFFT, Fs=self.sdr.sample_rate / 1e6, Fc=self.sdr.center_freq / 1e6)
            ind = 107 + np.argmax(pxx[107:111])        # largest power in the around 915.8 MHz
            power = 10*math.log10(pxx[ind])
            if iteration == 0:                         # the first sample is sometimes unnatrually high
                iteration += 1
                continue
            with open(self.output, 'a') as f:
                if self.timestamp == '':
                    lt = time.localtime()
                    f.write('{}-{}-{} {}:{}:{}, {:0.6f}\n'.format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, power))
                else: # for outdoor case, when the local times are not synchronized
                    ts = self.timestamp.split('-')
                    timestamp = '{}-{}-{} {}:{}:{}'.format(ts[0], ts[1], ts[2], ts[3], ts[4], ts[5])
                    f.write('{}, {:0.6f}\n'.format(timestamp, power))
            iteration += 1
            time.sleep(self.sleep)


    def sample_rss_loc(self, sample_iteration):
        '''Sample without animation, with location of sensor given.
        '''
        if os.path.exists(self.output) and os.path.getsize(self.output) > DEFAULT.rx_rss_file_max:
            os.remove(self.output)

        iteration = 0
        while iteration < sample_iteration or sample_iteration == -1:
            samples = self.sdr.read_samples(self.num_sample)
            pxx, _ = plt.psd(samples, NFFT=self.NFFT, Fs=self.sdr.sample_rate / 1e6, Fc=self.sdr.center_freq / 1e6)
            ind = 107 + np.argmax(pxx[107:111])     # largest power in the around 915.8 MHz
            power = 10*math.log10(pxx[ind])
            with open(self.output, 'a') as f:
                lt = time.localtime()
                f.write('{}-{}-{} {}:{}:{}, {:0.6f}, {} {}\n'.format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, power, self.x, self.y))
            iteration += 1
            time.sleep(self.sleep)


    def __call__(self, frame):
        '''update the animation
        Args:
            frame (int): this arg is mandatory, but useless by now
        '''
        from scipy.stats import norm

        self.ax0.cla()  # clear axis

        # read samples from sensor
        samples = self.sdr.read_samples(self.num_sample)

        # return the power in the linear scale (not log scale), and the corresponding frequences.
        pxx, freqs = self.ax0.psd(samples, NFFT=self.NFFT, Fs=self.sdr.sample_rate / 1e6, Fc=self.sdr.center_freq / 1e6)
        self.ax0.set_ylim([-50, 0])
        self.ax0.set_yticks(list(range(-50, 1, 5)))

        if frame >= 1:  # frame 0 is not a valid frame
            if frame % self.ax1_num == 0:
                self.ax1.cla()
                if os.path.exists(self.output) and os.path.getsize(self.output) > DEFAULT.rx_rss_file_max:
                    os.remove(self.output)
            ind = 107 + np.argmax(pxx[107:111])     # largest power in the around 915.8 MHz
            power = 10*math.log10(pxx[ind])
            with open(self.output, 'a') as f:
                lt = time.localtime()
                f.write('{}-{}-{} {}:{}:{}, {:0.6f}\n'.format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, power))
            print(frame, power, freqs[ind])
            self.power_peaks.append(power)
            self.freq_peaks.append(freqs[ind])
            if frame <= 10:
                return

            if len(self.power_peaks) >= self.ax1_num:
                mean = np.mean(self.power_peaks[-self.ax1_num:])
                std  = np.std(self.power_peaks[-self.ax1_num:])
                if len(self.power_peaks) >= self.ax1_num*2:
                    self.power_peaks = self.power_peaks[-self.ax1_num:]
                    self.freq_peaks = self.freq_peaks[-self.ax1_num:]
            else:
                mean = np.mean(self.power_peaks)
                std  = np.std(self.power_peaks)

            X = np.arange(mean - std*8, mean + std*8, 0.01)
            Y = norm(loc = mean, scale = std).pdf(X)
            self.ax1.plot(X, Y)
            self.ax1.set_xlabel('RSS')
            self.ax1.set_ylabel('Probability Density')
            self.ax1.set_title('Mean = {:.3f}, Std = {:.3f}'.format(mean, std))


if __name__ == '__main__':

    hint = 'Hint. python rx-sense.py -si 100 -sl 0.1 | ' + \
                 'python rx-sense.py -ani | ' + \
                 'python rx-sense.py -of /home/wings/caitao/rtl-testbed/rss -sl 0.05 -x 1.5 -y 4.5'

    parser = argparse.ArgumentParser(description = 'Receiver starts sensing RSS samples and save them to a file. ' + hint)
    parser.add_argument('-ani', '--animation', action='store_true', help = 'whether need animation. Useful when sensors is connected to a monitor')
    parser.add_argument('-si',  '--sample_iteration', type=int, nargs=1, default = [DEFAULT.rx_sample_iter], help = 'how many rss sampling iterations. -1 means unlimited iterations')
    parser.add_argument('-sl',  '--sleep', type=float, nargs=1, default=[DEFAULT.rx_sleep], help = 'how much time to sleep between two sample iterations')
    parser.add_argument('-of',  '--output_file', type=str, nargs=1, default=[DEFAULT.rx_rss_file], help='The output file to store the RSS samples')
    parser.add_argument('-x',   '--x_coord', type=float, nargs=1, default=[None], help='X coordinate of the receiver')
    parser.add_argument('-y',   '--y_coord', type=float, nargs=1, default=[None], help='Y coordinate of the receiver')
    parser.add_argument('-ts',  '--timestamp', type=str, nargs=1, default=[''], help='for outdoor, timestamp is received from the Tx machine')
    args = parser.parse_args()

    animate = args.animation
    sample_iteration = args.sample_iteration[0]
    sleep   = args.sleep[0]
    output  = args.output_file[0]
    x_coord = args.x_coord[0]
    y_coord = args.y_coord[0]
    timestamp = args.timestamp[0]

    sample_rate = DEFAULT.rx_sample_rate
    center_freq = DEFAULT.rx_center_freq
    gain        = DEFAULT.rx_gain
    num_samples = DEFAULT.rx_num_samples
    nfft        = DEFAULT.rx_NFFT
    ax1_num     = 10

    fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))
    rx = Receiver(ax0, ax1, ax1_num, sample_rate, center_freq, gain, num_samples, nfft, sleep, output, x_coord, y_coord, timestamp)

    if animate:
        import matplotlib.animation as anim
        print('animation = {}, iteraion = unlimited'.format(animate))
        anim = anim.FuncAnimation(fig, rx)
        plt.show()
    elif x_coord is not None and y_coord is not None:
        # print('animation = {}, iteration = {}, x = {}, y = {}'.format(animate, sample_iteration, x_coord, y_coord))
        time.sleep(2)
        rx.sample_rss_loc(sample_iteration)
        print('\n')
    else:
        # print('animation = {}, iteration = {}'.format(animate, sample_iteration))
        # start = time.time()
        rx.sample_rss(sample_iteration)
        # print('sampling time = {}'.format(time.time() - start))
