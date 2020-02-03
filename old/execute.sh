for i in {0..9..1}
do
	for j in {0..9..1}
	do
		echo $i $j
		parallel-ssh -h ~/arani_keys/list_of_addresses.txt -l odroid "rtl_sdr -f 916e6 -n 5e5 iq-$i$j.trial"
		parallel-ssh -h ~/arani_keys/addresses_r.txt -l pi "sudo -S rtl_sdr -f 916e6 -n 5e5 iq-$i$j.trial"
		read -p "Enter any key to continue"
	done
done
