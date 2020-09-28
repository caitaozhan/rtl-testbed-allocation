from subprocess import Popen, PIPE
import threading
import time
from default_config import DEFAULT
from test_interfere import TestInterfere
import json

def file_transmit():
    import os
    tx_name = os.uname()[1]
    for _ in range(60):
        time.sleep(1)
        lt = time.localtime()
        message = 'Hello, TX{}! {}-{}-{} {}:{}:{:d}\n'.format(tx_name, lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
        with open('file_transmit', 'w') as f:
            f.write(message)


def check_pur_connect():
    testinter = TestInterfere(DEFAULT.file_receive)
    interfere = testinter.test_interfere()
    if interfere is False:    # then the PUR is connected
        pur_info = {'discon':'False'}
    else:                     # the PUR is disconnected
        pur_info = {'discon':'True'}
    with open(DEFAULT.pur_info_file, 'w') as f:
        json.dump(pur_info, f)


if __name__ == '__main__':
    # start changing the file to transmit
    t = threading.Thread(target=file_transmit)
    t.start()

    # start PUR sensing
    command = ['python2', 'rx_text_ssh.py']
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    for i in range(60):
        if i == 7:
            check_pur_connect()
        time.sleep(1)
    p.kill()
    t.join()

