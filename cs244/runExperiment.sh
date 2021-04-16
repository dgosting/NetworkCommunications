#!/bin/bash

NUM_SERVERS=686
NUM_SWITCHES=(100 120 140 160 180 200 220 240 260 280 300)
NUM_SWITCH_PORTS=(8 8 10 10 10 12 12 12 12 12 12)
NUM_SERVER_PORTS=(8 8 6 6 6 4 4 4 4 4 4)
for i in $(seq 0 10)
do
    printf "Running experiment (%d, %d, %d, %d)\n" $NUM_SERVERS ${NUM_SWITCHES[$i]} ${NUM_SWITCH_PORTS[$i]} ${NUM_SERVER_PORTS[$i]}
    ./generateGraph.sh $NUM_SERVERS ${NUM_SWITCHES[$i]} ${NUM_SWITCH_PORTS[$i]} ${NUM_SERVER_PORTS[$i]}
done

gnuplot plotDense.plg
