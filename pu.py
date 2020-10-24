'''
Encapsulate a Primary User
'''

import random

class PU:
    '''Primary User
    '''
    def __init__(self, ip, hostname, x, y, gain, on):
        self.ip = ip
        self.hostname = hostname
        self.x = x
        self.y = y
        self.gain = gain
        self.on = on
        self.name= 'PU{}'.format(ip[-1])  # the IP address is static and I set it related to the PU name

    def get_loc(self):
        return '{}: ({}, {})'.format(self.name, self.x, self.y)

    def generate_gain(self):
        '''generate a random gain in a range. note that the PU are heterogeneous
        '''
        if self.name == 'PU1' or self.name == 'PU5':  # PU5 TX's power is weak. PU RX is easy to stop receiving when power is low
            self.gain = random.randint(75, 85)        # PU5 TX and RX need to be close to each other
        elif self.name == 'PU2':
            self.gain = random.randint(75, 85)
        elif self.name == 'PU3':                      # PU3 is very strong
            self.gain = random.randint(45, 50)
        elif self.name == 'PU4':
            self.gain = random.randint(55, 68)
        else:
            print("this PU name {} doesn't exits".format(self.name))

if __name__ == '__main__':
    pu = PU('1.1.1.1', 'caitao', 0, 0, 0, True)
    print(pu.get_loc())
