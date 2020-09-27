import argparse
import time


if __name__ == '__main__':

    lt = time.localtime()
    lt2 = time.localtime()

    description = 'Update the file to transmit with the latest time stamp. Hint: python file_transmit.py -n 2'

    parser = argparse.ArgumentParser(description = description)
    parser.add_argument('-n', '--name', type=int, nargs=1, default=[1], help='the name of the transmitter')
    args = parser.parse_args()

    tx_name = args.name[0]

    while True:
        time.sleep(1)
        lt = time.localtime()
        message = 'Hello, TX{}! {}-{}-{} {}:{}:{:d}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
        with open('file_transmit', 'w') as f:
            f.write(message)
            print message,
