#!/bin/bash

# Usage ./runExperiment.sh <# of servers> <# of switches> <# ports for switches> <ports for servers>
BUILD_DIR=experiment_$1_$2_$3_$4
GRAPH_FILE=$BUILD_DIR/$2_$3_graph.txt
TRAFFIC_FILE=$BUILD_DIR/$1_$2_$3_traffic.txt
DATA_FILE=$BUILD_DIR/$1_$2_$3_data.txt
STATS_FILE=stats.txt

mkdir $BUILD_DIR
printf "generating graph..."
python genGraph.py $2 $3 > $GRAPH_FILE
printf "DONE\ngenerating traffic..."
python genTraffic.py $1 $2 $4 > $TRAFFIC_FILE
printf "DONE\ncomputing shortest paths..."
python genPaths.py $GRAPH_FILE $TRAFFIC_FILE $STATS_FILE $1 $2 $3 > $DATA_FILE
printf "DONE\n"

gnuplot -e "filename='$DATA_FILE';outputFile='$BUILD_DIR/$1_$2_$3.png'" plotGraph.plg
