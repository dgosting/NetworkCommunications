#!/usr/bin/python

"""Custom topology example

Two directly connected switches plus two hosts for each switch to make a dumbbell shape:

             switch(s1)------ switch(s2)
               |                  |
               |                  |
             switch(s3)        switch(s4)
            /     \\          /      \\
      host(h1)  host(h2)   host(h3)   host(h4)


Adding the 'dumbbell' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=dumbbell' from the command line.
"""
import csv
from datetime import datetime
import itertools
import subprocess
import sys
import time
import os
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.node import OVSController
from mininet.util import quietRun
import matplotlib.pyplot as plt


class Dumbbell(Topo):

    def build(self, delay):

        # Add the switches (2 access and 2 backbone)
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        buffer_size = int(.2 * 21 * delay)

        # Link the left access router to the left backbone router
        self.addLink(s3, s1, bw=252, max_queue_size=buffer_size, use_htb=True)

        # Link the left and right backbone routers with a delay
        self.addLink(s1, s2, bw=984, delay=str(delay) + 'ms', use_htb=True)

        # Link the right access router to the right backbone router
        self.addLink(s4, s2, bw=252, max_queue_size=buffer_size, use_htb=True)

        # Link two hosts to the left access router
        self.addLink(h1, s3, bw=960)
        self.addLink(h2, s3, bw=960)

        # Link two hosts to the right access router
        self.addLink(h3, s4, bw=960)
        self.addLink(h4, s4, bw=960)


def run_test(algorithm, delay, run_time):
    # Clean up previous Mininet run
    os.system("sudo mn -c")

    kill_iperf = 'pkill iperf3'

    h1_iperf_file = "h1_iperf3_{0}_{1}ms.txt".format(algorithm, delay)
    h2_iperf_file = "h2_iperf3_{0}_{1}ms.txt".format(algorithm, delay)
    h3_iperf_file = "h3_iperf3_{0}_{1}ms.txt".format(algorithm, delay)
    h4_iperf_file = "h4_iperf3_{0}_{1}ms.txt".format(algorithm, delay)

    print("Creating topology with delay: {0}ms".format(delay))
    topo = Dumbbell(delay)

    # Create an instance of mininet and start it up
    net = Mininet(topo=topo, controller=OVSController, link=TCLink, autoSetMacs=True)

    print("Starting the Mininet instance")
    net.start()

    h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')

    # CLI(net)

    print("Starting Fairness test at", datetime.now().strftime("%H:%M:%S"))

    print("Starting TCP Flow #1")
    h3.cmd('nohup iperf3 -s -p 5001 &')
    h1.cmd('nohup iperf3 -c {0} -p 5001 -M 1500 -C {1} -t {2} -i 1 > {3} &'.format(h3.IP(), algorithm, run_time, h3_iperf_file))

    print("Starting TCP Flow #2")
    h4.cmd('nohup iperf3 -s -p 5002 &')
    h2.cmd('nohup iperf3 -c {0} -p 5002 -M 1500 -C {1} -t {2} -i 1 > {3} &'.format(h4.IP(), algorithm, run_time, h4_iperf_file))

    time.sleep(run_time + 2)

    h1.cmd(kill_iperf)
    h2.cmd(kill_iperf)
    h3.cmd(kill_iperf)
    h4.cmd(kill_iperf)

    time.sleep(2)

    print("Starting CWND test at", datetime.now().strftime("%H:%M:%S"))

    print("Starting TCP Flow #1")
    flow1_run_time = 2 * run_time
    h3.cmd('nohup iperf3 -s -p 5003 &')
    h1.cmd('nohup iperf3 -c {0} -p 5003 -i 1 -M 1500 -C {1} -t {2} > {3} &'.format(h3.IP(), algorithm, flow1_run_time, h1_iperf_file))

    offset = int(runtime * .25)

    print("Waiting {0} seconds...".format(offset))
    time.sleep(offset)

    print("Starting TCP Flow #2")
    flow2_run_time = int(1.75 * run_time)

    h4.cmd('nohup iperf3 -s -p 5004 &')
    h2.cmd('nohup iperf3 -c {0} -p 5004 -i 1 -M 1500 -C {1} -t {2} > {3} &'.format(h4.IP(), algorithm, flow2_run_time, h2_iperf_file))

    time.sleep(flow2_run_time + 2)

    h1.cmd(kill_iperf)
    h2.cmd(kill_iperf)
    h3.cmd(kill_iperf)
    h4.cmd(kill_iperf)
    net.stop()

    print("Finished test at ", datetime.now().strftime("%H:%M:%S"), ". Now parsing data from files....")


if __name__ == '__main__':

    algorithms = ['cubic'] # , 'reno', 'bbr', 'westwood']
    delays = [21] #, 81, 162]
    runtime = 1000

    for _algorithm in algorithms:
        for _delay in delays:
            run_test(_algorithm, _delay, runtime)


topos = {'dumbbell': (lambda: Dumbbell(21))}
