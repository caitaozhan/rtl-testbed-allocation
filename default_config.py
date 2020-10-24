'''
Default configurations
'''

class DEFAULT:
    '''Default configurations
    '''
    # Receiver (Sensor) side
    rx_sample_rate  = 2.4e6
    rx_center_freq  = 915.8e6
    rx_gain         = 0
    rx_num_samples  = 512*128
    rx_NFFT         = 256
    rx_rss_file     = '/home/odroid/rtl-testbed/rss'  # location of the rss samples
    rx_rss_file_max = 100e6                           # the maximum file size is 100MB
    rx_sample_iter  = 10                              # sample iterations (changed from 100 to 10 to speed up the spectrum allocation testbed)
    rx_sleep        = 0                               # sleep time between two iterations

    # Transmitter side
    tx_freq         = 915.8e6
    tx_gain         = 53
    tx_train_log    = 'tx_train_log'     # log for training
    tx_test_log     = 'tx_test_log'      # log for realtime localization testing
    tx_gps_log_raw  = 'gps_raw'
    tx_gps_log      = 'gps'

    # Localization  server side
    ser_rx_ip_file        = 'address/rx_ip'           # IP address for all the receivers
    ser_rx_ip_host_file   = 'address/rx_ip_host'
    ser_rx_data_dir       = 'rx_data'
    ser_rx_loc_file       = 'rx_data/hostname_loc_outdoor'
    ser_subnet_file       = 'address/subnet'
    ser_tx_ip_file        = 'address/tx_ip'
    ser_tx_ip_host_file   = 'address/tx_ip_host'
    ser_tx_log_dir        = 'tx_log'
    ser_training          = 'training'
    ser_tx_usernames      = ['caitao', 'wings']
    ser_tx_passwords      = ['zhan', 'trinitron']
    ser_tx_train_log_dir  = 'tx_log'
    ser_rx_train_data_dir = 'rx_data'

    # others
    loc_per_hypothesis    = 1    # for averaging
    wait_between_loc      = 2

    # PU/PUR
    pu_ip_host_file       = 'address/pu_ip_host'
    success_rate          = 80
    success_average       = 100
    pu_info_dir           = 'pu_info'
    pu_info_file          = 'pu_info/pu'
    pur_info_file         = 'pu_info/pur'
    su_type1_data         = 'training/su_pu'  # with SU info and PU data
    su_type2_data         = 'training/su_ss'  # with SU info and SS data
    file_transmit         = 'file_transmit'
    file_receive          = 'file_receive'
    su_same_loc_repeat    = 10

class MAP:
    name       = ''
    x_axis_len = 0
    y_axis_len = 0
    cell_len   = 0
    invalid_loc = []


class IndoorMap(MAP):
    '''Information of the indoor map:
    https://docs.google.com/presentation/d/1KogoR_itO4S4EDv2VTHTqzXgHjEs9eWwOUf7XRErIVI/edit?usp=sharing
    '''
    name       = 'Room 330'
    x_axis_len = 8     # the length of x axis
    y_axis_len = 6     # the length of y axis
    cell_len   = 1.22  # each cell's area is 1.22 x 1.22 m^2
    invalid_loc = []


class OutdoorMap(MAP):
    name       = 'South P'
    origin     = (40.896145, -73.127111)
    x_axis_len = 10
    y_axis_len = 10
    cell_len   = 3.2   # in meters

class HimanMap(MAP):
    name       = 'Himan'
    origin     = (40.861589, -73.291066)
    x_axis_len = 10
    y_axis_len = 10
    cell_len   = 2.4

class SplatMap(MAP):
    name       = 'Splat'
    origin     = (0, 0)
    x_axis_len = 40
    y_axis_len = 40
    cell_len   = 100   # in meters
