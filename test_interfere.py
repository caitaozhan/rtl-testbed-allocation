'''
Analyze the file_receive and see whether there is interference
'''

import time

class TestInterfere:

    def __init__(self, rx_file):
        self.rx_file = rx_file

    def test_interfere(self):
        '''If there is interfere, then return True. If no interfere, then return False
        '''
        timestamp1 = time.mktime(time.localtime())
        with open(self.rx_file, 'r') as f:
            start = time.time()
            lines = f.readlines()
            print('read file time = {}'.format(time.time() - start))
            i = 0
            for line in reversed(lines):
                line = line.split()
                if len(line) == 4:
                    time_str = ' '.join(line[2:])
                    try:
                        timestamp2 = time.mktime(time.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
                        diff = timestamp1 - timestamp2
                        if diff <= 5:   # once succussfull --> return False (no interfere)
                            return False
                    except:
                        pass
                i += 1
                if i >= 20:
                    break
        return True


def test():
    testinter = TestInterfere('file_receive')
    print(testinter.test_interfere())


if __name__ == '__main__':
    test()
