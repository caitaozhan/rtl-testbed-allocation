'''
Utlities
'''

class Utility:

    @staticmethod
    def extract_location(loc_str):
        '''
        Args:
            loc_str -- str: eg. (1.0, 2.0)
        Return:
            (float, float)
        '''
        loc_str = loc_str.replace(' ', '')
        loc_str = loc_str.replace('(', '')
        loc_str = loc_str.replace(')', '')
        x, y = loc_str.split(',')
        return float(x), float(y)

    @staticmethod
    def distance(point1, point2):
        '''
        Args:
            point1 -- (float, float)
            point2 -- (float, float)
        Return:
            float
        '''
        import math
        return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

    @staticmethod
    def gps_2_coordinate(gps, outdoormap):
        '''Get the coordinate according to the origin
        Args:
            gps -- tuple<float, float>
        return:
            tuple<float, float> -- the (x, y) cooridinate
        '''
        from mpu import haversine_distance
        a, b = gps
        lat_origin = outdoormap.origin[0]
        lon_origin = outdoormap.origin[1]
        y = haversine_distance((lat_origin, b), (a, b)) * 1000  # from km to m
        x = haversine_distance((a, lon_origin), (a, b)) * 1000
        y_sign = 1 if a > lat_origin else -1
        x_sign = 1 if b > lon_origin else -1
        try:
            return x_sign * x / outdoormap.cell_len, y_sign * y / outdoormap.cell_len
        except Exception as e:
            print(e)
            return -1, -1

    @staticmethod
    def guarantee_dir(directory):
        '''Gurantee that a directory exists
        Args:
            directory -- str
        '''
        import os
        if os.path.exists(directory) is False:
            os.mkdir(directory)


    @staticmethod
    def program_is_running(program):
        '''if tx_text.py is running the command will return a list of three elements
            ['caitao   23206 14243 99 20:26 pts/0    00:00:14 /usr/bin/python -u /home/caitao/Project/rtl-testbed-allocation/tx_text.py\n', 
            'caitao   23283 23280  0 20:26 pts/4    00:00:00 /bin/sh -c ps -ef | grep tx_text.py\n', 
            'caitao   23285 23283  0 20:26 pts/4    00:00:00 grep tx_text.py\n']
        '''
        from subprocess import Popen, PIPE
        command = 'ps -ef | grep {}'.format(program)
        p = Popen(command, shell=True, stdout=PIPE)
        p.wait()
        stdout = p.stdout.readlines()
        if len(stdout) >= 3:
            return True
        else:
            return False

    @staticmethod
    def program_is_running_t4():
        '''T4 has issues for killing the tx-text.py process when it is ran remotely. this issue is causing the program_is_running() function not working
           so here using an alternative just for T4: reading the pu_info/pu file
        '''
        import json
        from default_config import DEFAULT
        with open(DEFAULT.pu_info_file, 'r') as f:
            pu_info = json.loads(f.readlines()[0])
            if pu_info['tx_on'] == 'False':
                return False
            elif pu_info['tx_on'] == 'True':
                return True
            else:
                raise Exception("pu_info['tx_on'] value error")


    @staticmethod
    def get_command(describe):
        import platform
        if describe == 'speech':
            if platform.system() == 'Darwin':
                return 'say'
            elif platform.system() == 'Linux':
                return 'spd-say'
        if describe == 'pssh':
            if platform.system() == 'Darwin':
                return 'pssh'
            elif platform.system() == 'Linux':
                return 'parallel-ssh'
        raise Exception('No command returning')

    @staticmethod
    def test_lwan(private_net):
        '''test if the ip of this pc is in private_net
        '''
        from subprocess import Popen, PIPE
        command = "ifconfig | grep 'inet '"
        p = Popen(command, shell=True, stdout=PIPE)
        p.wait()
        stdout = p.stdout.readlines()
        for line in stdout:
            if line.find(private_net) != -1:
                return True
        return False

    @staticmethod
    def find_pid(program):
        from subprocess import Popen, PIPE
        command = 'ps -ef | grep {}'.format(program)
        p = Popen(command, shell=True, stdout=PIPE)
        p.wait()
        stdout = p.stdout.readlines()
        pids = []
        for line in stdout:
            if program in line and 'grep' not in line:
                line = line.split()
                pid = line[1]
                pids.append(pid)
        if not pids:
            return -1
        else:
            return pids


if __name__ == '__main__':
    # print(Utility.program_is_running('tx_text.py'))
    print(Utility.program_is_running_t4())
    # pid = Utility.find_pid('tx-text.py')
    # print(pid)
