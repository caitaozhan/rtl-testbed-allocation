# import pandas as pd
# import sys, os, string, threading
# import paramiko
# from multiprocessing.pool import ThreadPool
# import numpy as np
# #enable_host_logger()

# IP = 'IP'
# HOSTNAME = 'Hostname'
# cmd = "cd mallesh/rtl_fft && ./rtl_power_fftw -n 32 -q -b 256 -f 916e6"
# hackrf_ips = []

# def get_ip_list():
#     ip_hostfile = pd.read_csv('ip-hostfile.txt', sep=' ', header=None, names=[IP, HOSTNAME])
#     return ip_hostfile


# outlock = threading.Lock()

# def captureData(host):

#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     try:
#         ssh.connect(host, username='odroid', password='odroid')
#         stdin, stdout, stderr = ssh.exec_command(cmd)
#         stdin.flush()
#         linesList = stdout.readlines()
#         freq_list = np.zeros(len(linesList))
#         power_list = np.zeros(len(linesList))
#         for i in range(len(linesList)):
#             listofStrings = linesList[i].split(' ')
#             freq_list[i] = float(listofStrings[0])
#             power_list[i] = float(listofStrings[1])
#         highest_power_index = np.argmax(power_list)
#         actual_power = -65
#         if (freq_list[highest_power_index] > 9.1575e8 and freq_list[highest_power_index] < 9.158125e8):
#             actual_power = power_list[highest_power_index]
#     except Exception as e:
#         actual_power = -65

#     print(host, actual_power)
#     with outlock:
#         return actual_power

# def get_data(ip_host_map):
#     df = pd.DataFrame(columns=['ip', 'locations', 'frequency', 'power'])
#     pool = ThreadPool(5)
#     ip_list = list(ip_host_map['IP'])
#     ip_list = [ip[0:-1] for ip in ip_list]

#     results = pool.map(captureData, ip_list)
#     print(results)
#     pool.close()
#     pool.join()

# # def switch_hackrf(host, switchOn):
    
#     #print(linesList)
#     # for i in range(len(linesList)):
#     #     listofStrings = linesList[i].split(' ')
#     #     freq = float(listofStrings[0])
#     #     power = float(listofStrings[1])
#     #     #power = listofStrings[2]
#     #     #print(sensor_ips[i], freq, power)
#     #     if (freq > 9.1575e8 and freq < 9.158125e8):
#     #         rowsList.append([sensor_ips[i], locations[i], freq, power])
#     # df = pd.DataFrame(rowsList, columns=['ip', 'locatinons', 'frequency', 'power'])
#     # df.to_csv(filename)



# # def get_data(filename):
# #     df = pd.DataFrame(columns=['ip', 'locations', 'frequency', 'power'])
# #     stdout = []
# #     for host, host_out in output.items():
# #         try:
# #             for line in host_out.stdout:
# #                 stdout.append((host, line))
# #         except:
# #             pass
# #
# #     for host, host_out in output.items():
# #         try:
# #             client.host_clients[host].close_channel(host_out.channel)
# #         except:
# #             pass
# #     print(stdout)
#         #print(linesList)
#     #     for i in range(len(linesList)):
#     #         listofStrings = linesList[i].split(' ')
#     #         freq = float(listofStrings[0])
#     #         power = float(listofStrings[1])
#     #         #power = listofStrings[2]
#     #         #print(sensor_ips[i], freq, power)
#     #         if (freq > 9.1575e8 and freq < 9.158125e8):
#     #             rowsList.append([sensor_ips[i], locations[i], freq, power])
#     # df = pd.DataFrame(rowsList, columns=['ip', 'locatinons', 'frequency', 'power'])
#     # df.to_csv(filename)

# def get_user_input():
#     listOfLocations = range(0, 100)
#     i = 0
#     while True:
#         variable = input('Enter n to continue, s to repeat, q to quit')
#         if variable == 'n':
#             i += 1
#         get_data('L' + str(i))
#         print('Saving data to L' + str(i))
#         if variable == 'q':
#             return

# #get_user_input()
# ip_host_map = get_ip_list()
# get_data(ip_host_map)