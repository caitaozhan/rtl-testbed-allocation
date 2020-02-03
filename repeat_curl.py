'''
Copy input from the log, and repeat the realtime testing experiment.
'''

import sys
import argparse
from subprocess import Popen, PIPE

try:
    sys.path.append('../Localization')
    from input_output import Input
except ImportError as e:
    print(e)


def main1():
    while True:
        try:
            rawinput = raw_input('please copy input from the log:\n')
            port = raw_input('input port: 5000 is full training, 5001 is interpolation:\n')
            myinput = Input.from_json_str(rawinput)
            curl = "curl -d \'{}\' -H \'Content-Type: application/json\' -X POST http://localhost:{}/localize"
            command = curl.format(myinput.to_json_str(), port)
            p = Popen(command, stdout=PIPE, shell=True)
        except Exception as e:
            pass


def main2():
    parser = argparse.ArgumentParser(description='repeat the testbed experiment')
    parser.add_argument('-log', '--log_file', type=str, nargs=1, default=['results/10.22'], help='log file')
    # parser.add_argument('-log', '--log_file', type=str, nargs=1, default=['results/10.16.indoor-error'], help='log file')
    args = parser.parse_args()

    log_file = args.log_file[0]

    if log_file == '':
        while True:
            try:
                rawinput = raw_input('please copy input from the log:\n')
                myinput = Input.from_json_str(rawinput)
                curl = "curl -d \'{}\' -H \'Content-Type: application/json\' -X POST http://localhost:5000/localize"
                command = curl.format(myinput.to_json_str())
                p = Popen(command, stdout=PIPE, shell=True)
            except Exception as e:
                pass
    else:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    if line.strip() == '-':
                        break
                    myinput = Input.from_json_str(line)
                except:
                    print('not Input object')
                    continue
                print(myinput.to_json_str())
                # curl = "curl -d \'{}\' -H \'Content-Type: application/json\' -X POST http://localhost:5012/visualize"
                curl = "curl -d \'{}\' -H \'Content-Type: application/json\' -X POST http://localhost:5001/localize"
                command = curl.format(myinput.to_json_str())
                p = Popen(command, stdout=PIPE, shell=True)
                p.wait()



if __name__ == '__main__':
    
    main2()
    