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

        # Link the left and right backbone routers with a delay
        delayStr = str(delay) + 'ms'
        self.addLink(s1, s2, bw=984, delay=delayStr, use_htb=True)

        # Link the left access router to the left backbone router
        self.addLink(s1, s3, bw=252, max_queue_size=.2 * 21 * delay, use_htb=True)

        # Link the right access router to the right backbone router
        self.addLink(s2, s4, bw=252, max_queue_size=.2 * 21 * delay, use_htb=True)

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        # Link two hosts to the left access router
        self.addLink(h1, s3, bw=960)
        self.addLink(h2, s3, bw=960)

        # Link two hosts to the right access router
        self.addLink(h3, s4, bw=960)
        self.addLink(h4, s4, bw=960)


def parse_iperf_data(filename, offset):
    throughput = []
    cwnd = []

    if offset != 0:
        throughput = [0] * offset
        cwnd = [0] * offset

    with open(filename) as iperf_file:

        lines = iperf_file.readlines()

        for line_num in range(3, len(lines) - 6):
            line = lines[line_num].split()
            throughput.append(float(line[6]))

            cwnd_temp = float(line[9])
            cwnd_units = line[10]
            if cwnd_units.startswith("K"):
                cwnd_temp *= 1000
            else:
                cwnd_temp *= 1000000

            cwnd.append(cwnd_temp / 1500)

    time_data = [x for x in range(0, len(throughput))]

    return time_data, throughput, cwnd


def run_test(algorithm, delay, run_time):

    iperf_client_command = 'iperf3 -c {0} -p 5001 -i 1 -M 1500 -C {1} -t {2} > {3}'
    iperf_server_command = 'iperf3 -s -p 5001'
    run_in_background = ' &'
    kill_iperf = 'pkill iperf3'

    h1_iperf_file = "h1_iperf3_{0}_{1}ms_{2}.txt"
    h2_iperf_file = "h2_iperf3_{0}_{1}ms_{2}.txt"

    print("Creating topology with delay: {0}ms".format(delay))
    topo = Dumbbell(delay)

    # Create an instance of mininet and start it up
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)

    print("Starting the Mininet instance")
    net.start()

    h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')

    print("Starting Fairness test at", datetime.now().strftime("%H:%M:%S"))

    print("Starting TCP Flow #1")
    h1_fairness_file = h1_iperf_file.format(algorithm, delay, "fairness")
    h3.cmd(iperf_server_command + run_in_background)
    h1.cmd(iperf_client_command.format(h3.IP(), algorithm, run_time, h1_fairness_file) + run_in_background)

    print("Starting TCP Flow #2")
    h2_fairness_file = h2_iperf_file.format(algorithm, delay, "fairness")
    h4.cmd(iperf_server_command + run_in_background)
    h2.cmd(iperf_client_command.format(h3.IP(), algorithm, run_time, h2_fairness_file))

    time.sleep(2)

    h3.cmd(kill_iperf)
    h4.cmd(kill_iperf)

    print("Starting CWND test at", datetime.now().strftime("%H:%M:%S"))

    print("Starting TCP Flow #1")
    flow1_run_time = 2 * run_time
    h1_cwnd_file = h1_iperf_file.format(algorithm, delay, "cwnd")
    h3.cmd(iperf_server_command + run_in_background)
    h1.cmd(iperf_client_command.format(h3.IP(), algorithm, flow1_run_time, h1_cwnd_file) + run_in_background)

    offset = int(runtime * .25)

    print("Waiting {0} seconds...".format(offset))
    time.sleep(offset)

    print("Starting TCP Flow #2")
    flow2_run_time = int(1.75 * run_time)

    h2_cwnd_file = h2_iperf_file.format(algorithm, delay, "cwnd")
    h4.cmd(iperf_server_command + run_in_background)
    h2.cmd(iperf_client_command.format(h3.IP(), algorithm, flow2_run_time, h2_cwnd_file))

    time.sleep(2)

    h3.cmd(kill_iperf)
    h4.cmd(kill_iperf)
    net.stop()

    print("Finished test at ", datetime.now().strftime("%H:%M:%S"), ". Now parsing data from files....")

    # Parse the iperf data
    # h1_time, h1_throughput, h1_cwnd = parse_iperf_data(h1_iperf_file, 0)
    # h2_time, h2_throughput, h2_cwnd = parse_iperf_data(h2_iperf_file, offset)
    #
    # if is_cwnd_test:
    #     fig, ax = plt.subplots()
    #     ax.plot(h1_time, h1_cwnd, label="TCP Flow 1", linewidth=0.6)
    #     ax.plot(h2_time, h2_cwnd, label="TCP Flow 2", linewidth=0.6)
    #
    #     ax.set(xlabel='Time (seconds)',
    #            ylabel='Congestion Window (packets)',
    #            title=algorithm.upper() + " with Delay: " + str(delay) + "ms")
    #     ax.legend()
    #     file_name = "cwnd_" + algorithm + "_" + str(delay) + "ms.png"
    #     fig.savefig(file_name)
    # else:
    #     fig, ax = plt.subplots()
    #     ax.plot(h1_time, h1_throughput, label="TCP Flow 1", linewidth=0.6)
    #     ax.plot(h2_time, h2_throughput, label="TCP Flow 2", linewidth=0.6)
    #
    #     ax.set(xlabel='Time (seconds)',
    #            ylabel='Throughput (Mbps)',
    #            title=algorithm.upper() + " with Delay: " + str(delay) + "ms")
    #     ax.legend()
    #     file_name = "fairness_" + algorithm + "_" + str(delay) + "ms.png"
    #     fig.savefig(file_name)


if __name__ == '__main__':

    # Clean up previous Mininet run
    os.system("sudo mn -c")

    algorithms = ['cubic'] #, 'reno', 'bbr', 'westwood']
    delays = [21] #, 81, 162]
    runtime = 300

    for _algorithm in algorithms:
        for _delay in delays:
            run_test(_algorithm, _delay, runtime)


topos = {'dumbbell': (lambda: Dumbbell(21))}
