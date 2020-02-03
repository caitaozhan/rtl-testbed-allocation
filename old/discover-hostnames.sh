ncrack -p 22 --user odroid --pass odroid -iL address.txt | grep 130 | cut -d ' ' -f 6 >> hosts
pdsh -l odroid -w ^hosts -R ssh "hostname"
