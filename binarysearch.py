'''Binary search server.py to find the optimal gain
'''

from subprocess import Popen, PIPE
from default_config import DEFAULT

class BinarySearch:
    '''
    '''
    def __init__(self):
        pass

    def read_pu(self):
        '''read the info of PU/PUR, the {IP address: hostname}
        '''
        pu = {}
        with open(DEFAULT.pu_ip_host_file) as f:
            for line in f:
                line = line.split(':')
                pu[line[0]] = line[1].strip()
        return pu

    def search(self, low, high):
        pu = self.read_pu()
        ssh = "ssh {}@{} 'cd Project/rtl-testbed-allocation && python binary_search_helper.py -t 10'"
        for key, val in pu.items():
            command = ssh.format(val, key)
            print(command)
            p = Popen(command, shell=True)


def test():
    binarySearch = BinarySearch()
    binarySearch.search(1, 60)


if __name__ == '__main__':
    print()
    test()
