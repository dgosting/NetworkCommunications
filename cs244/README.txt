To run the experiment with preset configurations, run "sh runExperiment.sh". This will take approximately 10 minutes and run through 10 different network topologies.

To run custom experiment using different number of servers and switches, use “sh generateGraph.sh <# of servers> <# of switches> <# ports for switches> <# ports for servers>”

Make sure that the number of switches multiply by the number of ports for servers is greater than the number of servers, or else the topology is impossible to construct.

