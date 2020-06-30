'''
Tell all the receivers/sensors to do something
'''

import os
import platform
import argparse
import time
import glob
from subprocess import Popen, PIPE
from default_config import DEFAULT
from utility import Utility


class AllRx:
    '''Tell all the receivers/sensors to do something
    '''
    @staticmethod
    def sense(sample_iter, sleep, timestamp=False):
        '''Tell all the receivers to sense some RSS samples'''
        ssh_command = Utility.get_command('pssh')
        if timestamp is False:
            pssh = '{} -h {} -l odroid -t 0 -i \"cd rtl-testbed && python rx-sense.py -si {} -sl {}\"'
            command = pssh.format(ssh_command, DEFAULT.ser_rx_ip_file, sample_iter, sleep)
            print(command, '\n')
            p = Popen(command, shell=True, stdout=PIPE)
            p.wait()
            stdout = p.stdout.readlines()
            for i in range(0, len(stdout), 3):
                print stdout[i],
        else: # for the outdoor case, at the local time of odroids, the time is not synchronized
            lt = time.localtime()
            timestamp = '{}-{}-{}-{}-{}-{}'.format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
            pssh = '{} -h {} -l odroid -t 0 -i \"cd rtl-testbed && python rx-sense.py -si {} -sl {} -ts {}\"'
            command = pssh.format(ssh_command, DEFAULT.ser_rx_ip_file, sample_iter, sleep, timestamp)
            print(command, '\n')
            p = Popen(command, shell=True)
            p.wait()


    @staticmethod
    def update_github():
        '''Tell all the receivers to update code from GitHub'''
        pssh = 'parallel-ssh -h {} -l odroid -i \"cd rtl-testbed && git pull\"'
        command = pssh.format(DEFAULT.ser_rx_ip_file)
        print(command, '\n')
        p = Popen(command, shell=True)
        p.wait()

    @staticmethod
    def poweroff():
        '''poweroff the receivers one by one
        '''
        ssh = 'ssh -t odroid@{} sudo poweroff'
        with open(DEFAULT.ser_rx_ip_file, 'r') as f:
            for rx in f:
                command = ssh.format(rx.strip())
                print(command)
                p = Popen(command, shell=True)
                p.wait()



if __name__ == '__main__':

    description = 'Tell all the receivers/sensors to do something. ' + \
                  'Hint. python all_rx.py -ss | ' + \
                  'Hint. python all_rx.py -ug'

    parser = argparse.ArgumentParser(description = description)
    parser.add_argument('-ss', '--sense', action='store_true', help = 'tell all the receivers/sensors to sense RSS data')
    parser.add_argument('-si', '--sample_iteration', type=int, nargs = 1, default=[DEFAULT.rx_sample_iter], help = 'sampleing iterations')
    parser.add_argument('-sl', '--sleep', type=float, nargs = 1, default=[DEFAULT.rx_sleep], help = 'sleep between two iteration of RSS sampling')
    parser.add_argument('-ug', '--update_github', action='store_true', help = 'tell all the receivers/sensors to update repository from github')
    parser.add_argument('-po', '--poweroff', action='store_true', help='poweroff the receivers one by one')
    args = parser.parse_args()

    sense = args.sense
    update_github = args.update_github
    poweroff = args.poweroff

    if sense:                              # python all_rx.py -ss
        sample_iter = args.sample_iteration[0]
        sleep = args.sleep[0]
        AllRx.sense(sample_iter, sleep)
    if update_github:                      # python all_rx.py -ug
        AllRx.update_github()
    if poweroff:                           # python all_rx.py -po
        AllRx.poweroff()

    os.system('spd-say "finished"')
