'''Binary search at the {SU side} to find the optimal gain for SU
'''

import time
from subprocess import Popen, PIPE
from default_config import DEFAULT

class BinarySearch:
    '''
    '''
    def __init__(self, debug=False):
        self.debug = debug

    def read_pu(self):
        '''read the info of PU/PUR, the {IP address: hostname}
        '''
        pu = {}
        with open(DEFAULT.pu_ip_host_file) as f:
            for line in f:
                line = line.split(':')
                pu[line[0]] = line[1].strip()
        return pu

    def extract_stdout(self, stdout):
        '''stdout is from the PU, a list of strings
           [b'0 1 2 3 4 5 6 7 8 9 \n', b"('success count   threshold', 4)\n", 
           b"('success rate    threshold', 98)\n", b"('success average threshold', 500)\n", 
           b"('2020-6-17 0:8:3', 4145)\n", b"('2020-6-17 0:8:2', 3355)\n", 
           b"('2020-6-17 0:8:5', 3319)\n", b"('2020-6-17 0:8:4', 2985)\n", 
           b"('2020-6-17 0:8:6', 1768)\n", b"('fail_total', 67)\n", b"('success_counter', 5)\n", 
           b"('success_rate', 99.57158386086067)\n", b"('success_average', 3114)\n", 
           b"('success_total', 15572)\n", b'hostname =  T3\n', b'\n', b'RX disconnect =  False\n', 
           b'interfere =  False\n']
        '''
        pu_tx_on, hostname, disconnect, interfere = '', '', '', ''
        if self.debug:
            print(stdout)
        for line in stdout:
            line = str(line)
            if line.find('PU TX on') != -1:
                pu_tx_on = line.split('=')[1].strip()
                pu_tx_on = pu_tx_on.replace("\\n'", '')
            elif line.find('hostname') != -1:
                hostname = line.split('=')[1].strip()
                hostname = hostname.replace("\\n'", '')
            elif line.find('disconnect') != -1:
                disconnect = line.split('=')[1].strip()
                disconnect = disconnect.replace("\\n'", '')
            elif line.find('interfere') != -1:
                interfere = line.split('=')[1].strip()
                interfere = interfere.replace("\\n'", '')
        return {'hostname':hostname, 'pu_tx_on':pu_tx_on, 'disconnect':disconnect, 'interfere':interfere}


    def search(self, low, high):
        '''This is essentially finding the lower bound
        '''
        pu = self.read_pu()
        ssh = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python binary_search_helper.py -t 10'"
        su  = "hackrf_transfer -f {}  -x {}  -a 1 -c 60".format(DEFAULT.tx_freq, '{}')
        ps = []

        while low < high:
            # step 1: start the SU transmitter
            mid = (low + high + 1) // 2    # + 1 is the key for finding the lower bound
            print('--> left={}, mid={}, high={}'.format(low, mid, high))
            command = su.format(mid)
            p_su = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

            # step 2: start the PU/PUR and get all the stdout
            for key, val in pu.items():
                command = ssh.format(val, key)
                p = Popen(command, shell=True, stdout=PIPE)
                ps.append((p, command))
            pu_tx_on = []
            pur_disconnect = []
            interfere  = []
            while ps:
                new_ps = []
                for p, command in ps:
                    if p.poll() is not None:  # terminated
                        stdout = p.stdout.readlines()
                        print(command)
                        extract = self.extract_stdout(stdout)
                        pu_tx_on.append(extract['pu_tx_on'])
                        pur_disconnect.append(extract['disconnect'])
                        interfere.append(extract['interfere'])
                        print(extract, '\n')
                    else:
                        new_ps.append((p, command))      # still running
                ps = new_ps
                time.sleep(0.1)
            p_su.kill()

            # step 3: get the PU/PUR interfere results and update low or high
            if 'False' in pu_tx_on:
                print('exist PU TX off')
                return -1
            elif 'True' in pur_disconnect:
                print('exist PUR disconnected')
                return -1
            elif 'True' in interfere:
                high = mid - 1
            else: # no interfere
                low = mid
        return low


def test():
    binarySearch = BinarySearch(debug=False)
    print('optimal gain is', binarySearch.search(0, 47))


if __name__ == '__main__':
    test()
