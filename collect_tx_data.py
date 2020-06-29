'''
Collect Tx transmission log
'''

import os
import argparse
import time
import json
from default_config import DEFAULT
from subprocess import Popen, PIPE
from utility import Utility
from default_config import DEFAULT


class CollectTx:

    @staticmethod
    def get_tx_log(usernames, mode='train', num_log=1):
        '''Get the transmission log (ground truth) from Tx listed in the address list
        '''
        ssh_command = Utility.get_command('pssh')
        ps = []
        for username in usernames:
            ip_file = DEFAULT.ser_tx_ip_file + '.{}'.format(username)
            if os.stat(ip_file).st_size == 0:      # empty file
                continue
            if mode == 'train':
                pssh = "{} -t 5 -h {} -o {} -l {} -i \"cd Project/rtl-testbed && cat {}\""        # cat: the entire log
                command = pssh.format(ssh_command, ip_file, DEFAULT.ser_tx_log_dir, username, DEFAULT.tx_train_log)
            elif mode == 'test':
                pssh = "{} -h {} -o {} -l {} -i \"cd Project/rtl-testbed && tail -{} {}\""    # tail: the latest log
                command = pssh.format(ssh_command, ip_file, DEFAULT.ser_tx_log_dir, username, num_log, DEFAULT.tx_test_log)
            else:
                raise Exception('mode = {} invalid'.format(mode))
            print(command)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append(p)
        for p in ps:
            p.wait()


    @staticmethod
    def discover_hosts(subnet_file, usernames, passwords):
        '''
        Discover all hosts in a subnet whose credentials are username and password
        Calling following commands:
        1) ncrack -p 22 --user odroid --pass odroid -iL addresses.txt | grep -oE "regular expression for ip address" >> hosts
        2) pdsh -l odroid -w ^hosts -R ssh "hostname"
        Args:
            subnet_file (str):
            usernames (list<str>):
            passwords (list<str>):
        '''
        if len(usernames) != len(passwords):
            raise Exception('length of usernames and passwords are different')
        if os.path.isfile(subnet_file) is False:
            raise Exception('subnet file not found')

        #step 1: ncrack, get IP address
        regex_ip = r"^([0-9]{1,3}\.){3}[0-9]{1,3}"
        ncrack = "ncrack -p 22 --user {} --pass {} -iL {} -gto=12s | grep -oE \"{}\""
        ps = []

        for username, password in zip(usernames, passwords):
            command = ncrack.format(username, password, subnet_file, regex_ip)
            print(command)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append((p, username))

        for p, username in ps:
            p.wait()
            ip_file = open(DEFAULT.ser_tx_ip_file + '.{}'.format(username), 'w')
            for line in p.stdout:
                ip_file.write(line)
            ip_file.close()

        # step 2: pdsh, get hostname for each IP
        pdsh = "pdsh -l {} -w ^{} -R ssh \"hostname\""
        ps = []

        for username in usernames:    # no password because the hosts have my ssh public key
            command = pdsh.format(username, DEFAULT.ser_tx_ip_file + '.{}'.format(username))
            print(command)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append((p, username))

        for p, username in ps:
            p.wait()
            ip_host_file = open(DEFAULT.ser_tx_ip_host_file + '.{}'.format(username), 'w')
            for line in p.stdout:
                ip_host_file.write(line)
            ip_host_file.close()

    @staticmethod
    def get_pu_info():
        '''get the information of PU, including location and transmitting power
        '''
        pu = {}
        with open(DEFAULT.pu_ip_host_file, 'r') as f:
            for line in f:
                line = line.split(':')
                pu[line[0]] = line[1].strip()
        ssh = "ssh {}@{} 'cd Project/rtl-testbed-allocation && cat {}'"
        ps = []
        for ip, hostname in pu.items():
            command = ssh.format(hostname, ip, DEFAULT.pu_info_file)
            p = Popen(command, shell=True, stdout=PIPE)
            ps.append((p, command))
        pu_info = []
        while ps:
            new_ps = []
            for p, command in ps:
                if p.poll() is not None:  # terminated
                    stdout = p.stdout.readlines()
                    pu_info.append(json.loads(stdout[0]))
                else:
                    new_ps.append((p, command))
            ps = new_ps
            time.sleep(0.1)
        return pu_info


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Collect data from transmitters')
    parser.add_argument('-dh', '--discover_hosts', action='store_true', help='discover IP and hostname of transmitters')
    parser.add_argument('-tl', '--transmit_log', action='store_true', help='get the transmission log of the transmitters')
    parser.add_argument('-mo', '--mode', type=str, nargs=1, default=['train'], help='training mode or testing localization mode. they have different logging behavior')
    args = parser.parse_args()

    discover  = args.discover_hosts
    trans_log = args.transmit_log
    mode      = args.mode[0]

    subnet_file = DEFAULT.ser_subnet_file
    usernames = DEFAULT.ser_tx_usernames
    passwords = DEFAULT.ser_tx_passwords

    if discover:
        try:
            CollectTx.discover_hosts(DEFAULT.ser_subnet_file, usernames, passwords)
        except Exception as e:
            print(e)
    elif trans_log:
        try:
            CollectTx.get_tx_log(usernames, mode)
        except Exception as e:
            print(e)
    else:
        print('no action')
