from utility import Utility
from subprocess import Popen


if __name__ == '__main__':

    # step 1: find the pid
    program = 'rx_text_ssh.py'
    pids = Utility.find_pid(program)

    # step 2: kill the previous program if pid is not -1
    if pids != -1:
        for pid in pids:
            command = 'kill {}'.format(pid).split()
            p = Popen(command)
            print('{} killed'.format(pid))
