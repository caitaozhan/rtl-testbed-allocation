'''
Collect data from sensors
'''

from subprocess import Popen, PIPE
import os
import platform
import time
import argparse
from default_config import DEFAULT
from utility import Utility


class CollectRx:

    @staticmethod
    def discover_hosts(subnet_file, usernames, passwords, cores=4):
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
        ip_file = open(DEFAULT.ser_rx_ip_file, 'w')
        ps = []

        for username, password in zip(usernames, passwords):
            command = ncrack.format(username, password, subnet_file, regex_ip)
            print(command)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append(p)

        for p in ps:
            p.wait()
            for line in p.stdout.read():
                ip_file.write(line)

        ip_file.close()

        # step 2: pdsh, get hostname for each IP
        pdsh = "pdsh -l {} -w ^{} -R ssh \"hostname\""
        ip_host_file = open(DEFAULT.ser_rx_ip_host_file, 'w')
        ps = []

        for username, _ in zip(usernames, passwords):    # no password because the hosts hav my ssh public key
            command = pdsh.format(username, DEFAULT.ser_rx_ip_file)
            print(command)
            p = Popen(command, stdout=PIPE, shell=True)
            ps.append(p)

        for p in ps:
            p.wait()
            for line in p.stdout:
                ip_host_file.write(line)

        ip_host_file.close()


    @staticmethod
    def get_rss_data(num_samples):
        '''Get RSS from some sensors listed in the address list. Save them to files, whose filename is the IP address
        Calling following command:
        1) time parallel-ssh -h list_of_address -o output -l odroid -i "tail -3 /tmp/rss"
        Args:
            num_samples (int): number of samples
        '''
        ssh_command = Utility.get_command('pssh')
        pssh = "{} -h {} -o {} -l odroid -i \"tail -{} {}\""
        command = pssh.format(ssh_command, DEFAULT.ser_rx_ip_file, DEFAULT.ser_rx_data_dir, num_samples, DEFAULT.rx_rss_file)
        print(command)
        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        p.wait()



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Collect data from sensors')
    parser.add_argument('-dh', '--discover_hosts', action='store_true', help = 'Wheather to discover IP and hostname of sensors')
    parser.add_argument('-ns', '--num_samples', type = int, nargs = 1, default = [3], help = 'Number of samples to collect at each time')
    args = parser.parse_args()

    discover    = args.discover_hosts
    num_samples = args.num_samples[0]

    subnet_file = DEFAULT.ser_subnet_file
    usernames   = ['odroid']
    passwords   = ['odroid']

    try:
        # if discover:          # discover IP and hostname
        if discover:
            print('discover IP and hostnames')
            CollectRx.discover_hosts(subnet_file, usernames, passwords)
        else:                 # collect RSS data from sensors
            print('collect RSS data from each host(receiver/sensor), number of samples = {}'.format(num_samples))
            CollectRx.get_rss_data(num_samples)
    except Exception as e:
        print(e)
