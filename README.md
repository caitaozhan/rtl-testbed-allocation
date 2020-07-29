# rtl-testbed
testbed related stuffs.

# TODO
1. sensor 140, 160 seems to have lower RSS than others
2. some antennas are loose
3. outdoor localize algo: tx and rx same, RSS can be somewhat different
2. Plot (data preparation stage done)
3. 9.27 task: {1,2,3} Tx experiment with interpolated training data, train again to test the interpolation error (interpolation error is not done)


## Setup USRP
1) Go to [website](https://kb.ettus.com/Building_and_Installing_the_USRP_Open-Source_Toolchain_(UHD_and_GNU_Radio)_on_Linux). A large list of packages to install
2) sudo apt-get install uhd*
3) sudo uhd_images_downloader
4) sudo apt-get install gnuradio gnuradio-dev libgnuradio-uhd3.7.11 (listed by sudo apt-get install gnuradio*)

## Setup HackRF
1) sudo apt install hackrf libhackrf-dev
2) run: sudo hackrf_transfer -f 915800000  -x 40  -a 1 -c 60

## Setup Odroid
1) Download the live OS: https://wiki.odroid.com/getting_started/os_installation_guide#tab__odroid-c2. Extract and also decompress it.
2) sudo dd if='***.img' of=/dev/mmcblk0 bs=4M
3) install rtl-sdr: sudo apt install rtl-sdr && pip install pyrtlsdr
4) install rtl_fftw
5) Setup hostname
6) ssh: give my destop's ssh to odroid, give odroid's ssh to my github account.
7) git clone git@github.com:caitaozhan/rtl-testbed.git

NOTE: 08/20/2019. The odroid C2 18.04 has issues with python and git. Archiconda might help. Git cannot be installed.

## Crowdsourced (Ideas)
1) Heterogeneity in terms of cost and gain.
2) Cost ideas: power measurements and introduce online selection.
3) Connectivity issue: mesh network?
4) gain ideas: calibration by known background transmittes.


Just consider the Rx. Affecting RSS:
Software side: rtl-sdr sample rate, and gain.
hardware side: rtl-sdr anatena length (the anatena can shrink) and and device height (on the floor or table), antenna angle, spinning the base
Small scale fading effect is huge.


## time measurements

-si 5
[6.2, 7.4, 7.3, 6.5, 6.3]              avg = 6.74

-si 10
[7.2, 7.2, 7.8, 9.7, 7.2, 6.9, 6.9]    avg = 7.56

odroid side
[5.4, 5.5, 5.3, 5.4, 5.3]              avg = 5.38

odroid side optmize-1 (reduce import)
[4.6, 4.5, 4.6, 4.6, 4.7]              avg = 4.6


## Notes
python 2
|Steps|Indoor Commands|Outdoor Commands|
|--|--|--|
|discover Rx hosts|python collect_rx_data.py -dh| <--|
|discover Tx hosts|python collect_tx_data.py -dh| <--|
|training (Tx)|python tx-run-wrapper.py -n 1 -g 45 -mo train|python tx-run-wrapper.py -n 1 -g 45 -gps -mo train|
|training (Rx)|python training.py -si 10 -sl 0.01 -avg 4 -wt 4| python training.py -si 10 -sl 0.01 -avg 3 -wt 4 -ts|
|generate localization input (full)|python train.py -mydir 9.26 -src testbed-indoor||
|check if data is complete, watch out for zero RSS data sensor at a location|manually fix it||
|generate localization input (inter)|python train.py -mydir 9.26.inter -src testbed-indoor -inter idw||
|generate localization input (sub)|python train.py -src testbed-indoor -full 9.26.inter -sub 9.26.inter-sub||
|Update localization server configurations and run it|use vscode||
|testing: run Tx|python tx-run-wrapper.py -n 1 -g 45 -mo test||
|testing: run client|python realtime_testing.py -num 1 -src testbed-indoor -met our splot -avg 4 -wt 2 -en 1||

## Introduction about GNU Radio and USRP
[GNU Radio official wiki website](https://wiki.gnuradio.org/index.php/Main_Page)

[Ettus Research homepage](https://kb.ettus.com/Knowledge_Base)

[A master thesis](http://oa.upm.es/21618/1/TESIS_MASTER_LEI_ZHANG.pdf)


# increase the interfere bar, not lower
# decrease the distance between PU and PUR, so I can lower the PU gain

# the first colomn of the data is number of PU
# automate the PU commands
# the lenovo laptop is "weaker" than others

# did hackrf T3 deteriate? need to re-calibrate all the TXs
# the small cart, remove the middle level
# test the sensor with two antenna, when TX is tx_text. Is it different than tx-run?
# mac terminator-like stuff?
# antenna being long better?

# host-200 has issues, host 188 no wifi dongle?
# the issue of PU affecting each other
