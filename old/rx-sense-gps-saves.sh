while true
do
	sudo rtl_sdr -f 916e6 -n 5e6 $(sudo grep -m 1 GPGLL /dev/ttyACM0)$.iq
	sleep 1
done

