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
        self.addLink(s1, s2, bw=984, cls=TCLink, delay=delayStr, max_queue_size=82 * delay, use_htb=True)

        # Link the left access router to the left backbone router
        self.addLink(s1, s3, bw=252, cls=TCLink, delay='0ms', max_queue_size=.2 * 21 * delay, use_htb=True)

        # Link the right access router to the right backbone router
        self.addLink(s2, s4, bw=252, cls=TCLink, delay='0ms', max_queue_size=.2 * 21 * delay, use_htb=True)

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        # Link two hosts to the left access router
        self.addLink(h1, s3, cls=TCLink, bw=960)
        self.addLink(h2, s3, cls=TCLink, bw=960)

        # Link two hosts to the right access router
        self.addLink(h3, s4, cls=TCLink, bw=960)
        self.addLink(h4, s4, cls=TCLink, bw=960)


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


def run_test(algorithm, delay, run_time, offset, is_cwnd_test):

    iperf_command = 'iperf3 -c {0} -p 5001 -i 1 -4 -M 1460 -N -w 16m -C {1} -t {2} --logfile {3}'

    test_name = "fairness"

    if is_cwnd_test:
        print("Running CWND Test:")
        test_name = "cwnd"
    else:
        print("Running Fairness Test:")

    h1_iperf_file = "h1_iperf3_{0}_{1}ms_{2}.txt".format(algorithm, delay, test_name)
    h2_iperf_file = "h2_iperf3_{0}_{1}ms_{2}.txt".format(algorithm, delay, test_name)

    os.system("sudo mn -c")

    now = datetime.now()
    print("Starting Test at", now.strftime("%H:%M:%S"), "which will run for", run_time, "seconds.")

    # Create the topology using the specified delay
    topo = Dumbbell(delay)

    # Create an instance of mininet and start it up
    net = Mininet(topo=topo)
    net.start()

    try:
        time.sleep(2)

        # Get references to all 4 hosts
        h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
        commands = dict()

        # Start iperf server on receiver hosts
        print("Starting servers on receiving hosts")
        commands[h3] = h3.popen(['iperf3', '-s', '-p', '5001', '-4'])
        commands[h4] = h4.popen(['iperf3', '-s', '-p', '5001', '-4'])

        # start iperf clients on client hosts
        h1_command = iperf_command.format(h3.IP(), algorithm, run_time, h1_iperf_file)

        if is_cwnd_test:
            offset_time = run_time - offset
            h2_command = iperf_command.format(h4.IP(), algorithm, offset_time, h2_iperf_file)
        else:
            h2_command = iperf_command.format(h4.IP(), algorithm, run_time, h2_iperf_file)

        # Pause main thread a few seconds to allow servers to startup
        time.sleep(5)

        print("Starting client on h1")
        commands[h1] = h1.popen(h1_command, shell=True)

        if is_cwnd_test:
            time.sleep(offset)
            print("Starting delayed client on h2")
        else:
            print("Starting client on h2 immediately")

        commands[h2] = h2.popen(h2_command, shell=True)

        time.sleep(run_time - offset + 30)

        # Kill the server iperf processes
        commands[h1].terminate()
        commands[h2].terminate()

        # Kill the server iperf processes
        commands[h3].terminate()
        commands[h4].terminate()

    except:
         print("Exception occurred")

    net.stop()

    print("Finished test at ", datetime.now().strftime("%H:%M:%S"), ". Now parsing data from files....")

    # Parse the iperf data
    h1_time, h1_throughput, h1_cwnd = parse_iperf_data(h1_iperf_file, 0)
    h2_time, h2_throughput, h2_cwnd = parse_iperf_data(h2_iperf_file, offset)

    if is_cwnd_test:
        fig, ax = plt.subplots()
        ax.plot(h1_time, h1_cwnd, label="TCP Flow 1", linewidth=0.6)
        ax.plot(h2_time, h2_cwnd, label="TCP Flow 2", linewidth=0.6)

        ax.set(xlabel='Time (seconds)',
               ylabel='Congestion Window (packets)',
               title=algorithm.upper() + " with Delay: " + str(delay) + "ms")
        ax.legend()
        file_name = "cwnd_" + algorithm + "_" + str(delay) + "ms.png"
        fig.savefig(file_name)
    else:
        fig, ax = plt.subplots()
        ax.plot(h1_time, h1_throughput, label="TCP Flow 1", linewidth=0.6)
        ax.plot(h2_time, h2_throughput, label="TCP Flow 2", linewidth=0.6)

        ax.set(xlabel='Time (seconds)',
               ylabel='Throughput (Mbps)',
               title=algorithm.upper() + " with Delay: " + str(delay) + "ms")
        ax.legend()
        file_name = "fairness_" + algorithm + "_" + str(delay) + "ms.png"
        fig.savefig(file_name)


if __name__ == '__main__':
    _algorithm = sys.argv[1]
    _delay = int(sys.argv[2])
    _runtime = int(sys.argv[3])
    _offset = int(sys.argv[4])

    run_test(_algorithm, _delay, _runtime / 2, 0, False)
    run_test(_algorithm, _delay, _runtime, _offset, True)

    # algorithms = ['cubic'] #, 'reno', 'htcp', 'bic']
    # delays = [21] #, 81, 162]
    # runtime = 600
    # _offset = 75
    #
    # for _algorithm in algorithms:
    #     for _delay in delays:
    #         run_test(_algorithm, _delay, runtime / 2, 0, False)
    #         run_test(_algorithm, _delay, runtime, _offset, True)


topos = {'dumbbell': (lambda: Dumbbell(21))}
