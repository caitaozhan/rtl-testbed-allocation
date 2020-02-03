'''
The sensor data on 10.6 night is missing comma
'''

import glob
import shutil
import os

def add_comma(inputfile, outputfile):
    '''
    '''
    with open(inputfile, 'r') as inpt, open(outputfile, 'w') as output:
        for line in inpt:
            line = line.split(' ')
            output.write(line[0])
            output.write(' ')
            output.write(line[1])
            output.write(', ')
            output.write(line[2])


if __name__ == "__main__":
    directory = '../rx_data'
    tmp_dir = 'tmp'
    os.chdir(directory)

    if os.path.exists(tmp_dir) is False:
        os.mkdir(tmp_dir)

    for ip in glob.glob('*.*.*.*'):
        add_comma(ip, tmp_dir + '/' + ip)
