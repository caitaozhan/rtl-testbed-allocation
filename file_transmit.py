import time
import os


if __name__ == '__main__':
    description = 'Update the file to transmit with the latest time stamp. Hint: python file_transmit.py'
    tx_name = os.uname()[1]

    for _ in range(1000):
        time.sleep(1)
        lt = time.localtime()
        message = 'Hello, TX{}! {}-{}-{} {}:{}:{:d}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
        with open('file_transmit', 'w') as f:
            f.write(message)
            print message,
