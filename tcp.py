#!/usr/bin/python

# EEE4121F-B Lab 1
# TCP
# Modified from https://github.com/mininet/mininet/wiki/Bufferbloat

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from statistics import mean, stdev

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen
import termcolor as T

import sys
import os
import math


# TODO: Don't just read the TODO sections in this code.  Remember that
# one of the goals of this lab is for you to learn how to use
# Mininet. :-)

parser = ArgumentParser(description="TCP tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default 
# For the first experiments we want to investigate Reno Behaviour
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# This  only needs to be changed for the TCP BBR experiments                    
parser.add_argument('--qman',
                    help="Queue management algorithm to use",
                    default="pfifo_fast")


# Expt parameters
args = parser.parse_args()

class TCPTopo(Topo):
    "Simple topology for TCP experiment."

    def build(self, n=2):
        # TODO1: create two hosts
        
        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # TODO2: Add links with appropriate characteristics
        self.addLink(h1, switch, bw=args.bw_host, delay=args.delay, max_queue_size=args.maxq)
        self.addLink(h2, switch, bw=args.bw_net, delay=args.delay, max_queue_size=args.maxq)
        
        return

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!
def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > %s/%s" % (args.dir, outfile),shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
    
    # TODO4: Retrieve the hosts, replace with appropriate names
    # There should be two hosts, one is added already
    h1 = net.get('h1')
    h2 = net.get('h2')
    
    
    print("Starting iperf server...")
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    
    server = h1.popen("iperf -s -w 16m")
    server2 = h2.popen("iperf -s w 16m")

    # TODO4: Start the iperf client on h1 and h2.  Ensure that you create two
    # long lived TCP flows in both directions (one is already created above)
    h2.cmd("iperf -c %s -t %s" % (h1.IP(), args.time))
    h1.cmd("iperf -c %s -t %s" % (h2.IP(), args.time))

def start_webserver(net):
    server = net.get('h1')
    proc = server.popen("python http/webserver.py", shell=True)
    sleep(1)
    return [proc]

def start_ping(net):
    # TODO5: Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this https://linux.die.net/man/8/ping

    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    h1 = net.get('h1')
    h2 = net.get('h2')
    ping_train =  h1.popen("ping -c %s -i 0.1 %s > %s/ping.txt" % (args.time*10, h2.IP(), args.dir), shell=True)
    ping_train.communicate() #start the ping train
    

# Use function to measure time it takes to complete webpage transfer
def times(net, h1, h2):
	store = []
	webserver_ip = h1.IP()
	# measure time to complete transfer between hosts 3 times
	for i in range(3):
		command = "curl -o index.html -s -w %%{time_total} %s/http/index.html" % webserver_ip
		fetch = h2.popen(command, shell=True, stdout=PIPE)
		var = float(fetch.stdout.read())
		store.append(var)

	#average = mean(store) # get average time to complete webpage transfer

	return mean(store)

def tcp():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    os.system("sysctl -w net.core.default_qdisc=%s" % args.qman)
    topo = TCPTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # Start all the monitoring processes
    # start_tcpprobe("cwnd.txt")

    # TODO3: Start monitoring the queue sizes.  Since the switch I
    # created is "switch", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))

    # TODO4: Start iperf 
    s_iperf = Process(target=start_iperf, args=(net,))
    s_iperf.start()

    # TODO5: Start ping trains
    s_ping = Process(target=start_ping, args=(net,))
    s_ping.start()
    start_webserver(net)

    # TODO6: measure the time it takes to complete webpage transfer
    # from h1 to h2 (say) 3 times.  Hint: check what the following
    # command does: curl -o /dev/null -s -w %{time_total} google.com
    # Now use the curl command to fetch webpage from the webserver you
    # spawned on host h1 (not from google!)

    # Hint: have a separate function to do this and you may find the
    # loop below useful.

    time_taken = []
    start_time = time()
    h1 = net.get('h1')
    h2 = net.get('h2')

    while True:
        # do the measurement (say) 3 times.
        time_taken.append(times(net, h1, h2))
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print("%.1fs left..." % (args.time - delta))
    
       
    # TODO: compute average (and standard deviation) of the fetch
    # times.  

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    #CLI(net)

    average = mean(time_taken)
#    std_dev = stdev(time_taken)

    # Print answers to the screen
    print("Average: %s seconds \n" % average)
#    print("Standard deviation: %s seconds \n" % std_dev)

    stop_tcpprobe()
    qmon.terminate()
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    tcp()

