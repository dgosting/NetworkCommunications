#!/bin/bash

# Generates a random permutation traffic matrix
# Usage ./genTraffic.py <# of servers> <# of switches> <# of ports per switch>
import random, sys

def checkShuffle(output) :
    for i in range(0, len(output)) :
        if output[i] == i :
            return False
    return True

def genTrafficMatrix(num_servers, num_switches, degree) :
    assignment = {}
    switchCounts = [0] * num_switches
    send = range(0, num_servers)
    receive = range(0, num_servers)
    for i in range(0, num_servers) :
        switch = random.randint(0, num_switches - 1)
        while (switchCounts[switch] == degree) :
            switch = random.randint(0, num_switches - 1)
        switchCounts[switch] = switchCounts[switch] + 1
        assignment[i] = switch
    receive = range(0, num_servers)
    random.shuffle(receive)
    while not checkShuffle(receive) :
        random.shuffle(receive)
    result = []
    for i in range(0, num_servers) :
        result.append((assignment[send[i]], assignment[receive[i]]))
    return result

servers = int(sys.argv[1])
switches = int(sys.argv[2])
ports = int(sys.argv[3])

traffic = genTrafficMatrix(servers, switches, ports)
for i in range(0, len(traffic)) :
    print str(traffic[i])[1: -1]
