#!/bin/bash

set -e

# You can change these parameters:
bwhost=1000
qsize=100
cong=bbr

# These parameters do not change:
bwnet=2
delay=50
dir=./
time=30
qman=fq

# Now start the experiment and load the parameters
echo "The experiment is running..."
echo "Queue size is" $qsize "and host speed is" $bwhost "Mbps..."
python tcp.py --bw-host=$bwhost \
		--bw-net=$bwnet \
		--delay=$delay \
		--dir=$dir \
		--time=$time \
		--maxq=$qsize \
#		--cong=$cong\
#		--qman=$qman\

echo "Done. Plotting graphs now..."
echo "Plotting ping graph..."
python plot_ping.py -f $dir./ping.txt -o $dir./rtt.png
echo "Done."

echo "Plotting queue graph..."
python plot_queue.py -f $dir./q.txt -o $dir./queue.png
echo "Done."
echo "The experiment is now complete."

