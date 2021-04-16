#!/bin/bash

# Generates a uniformly random regular graph consisting of n nodes with x number of links per node

# Usage: ./genGraph <# of nodes> <# of links per node>

import random, sets, sys, math

# checks if the current graph is fully connected given the links left over
def fullyConnected(g, links):
	nodes = links.keys()
	for i in range(0, len(nodes)) :
		for j in range(i + 1, len(nodes)) :
			if (nodes[j] not in g[nodes[i]]) :
				return False
	return True

# generate a regular random graph consisting of n nodes and k links per node
def genGraph(n, k) :
	links = {}
	g = {}
	for i in range(0,n) :
		links[i] = k
		g[i] = sets.Set([])
	while len(links) > 1:
		# randomly select 2 nodes
		randomSample = random.sample(links.items(), 2)
		(nodeA, kA) = randomSample[0]
		(nodeB, kB) = randomSample[1]
		# check if the 2 nodes are already connected
		if (nodeB in g[nodeA]) :
			# the graph is fully connected, we need to remove some links
			if (fullyConnected(g, links)) :
				# randomly remove a current link
				a = random.randint(0, len(g) - 1)
				while (a == nodeA or a == nodeB or a in g[nodeA] or len(g[a] - g[nodeB].union([nodeA, nodeB])) == 0) :
					a = random.randint(0, len(g) - 1)
				b = random.choice(list(g[a]))
				while (b == nodeA or b == nodeB or b in g[nodeB]) :
					b = random.choice(list(g[a]))
				g[a].remove(b)
				g[b].remove(a)
				g[a].add(nodeA)
				g[nodeA].add(a)
				g[b].add(nodeB)
				g[nodeB].add(b)
			else :
				continue
		# assume all links are bidirectional
		g[nodeA].add(nodeB)
		g[nodeB].add(nodeA)
		# update the number of free links for each node
		if kA == 1:
			del links[nodeA]
		else :
			links[nodeA] = kA - 1
		if kB == 1:
			del links[nodeB]
		else :
			links[nodeB] = kB - 1
	# check if there is a single switch with more than 2 unmatched ports
	if (len(links) == 1) :
		(node, linksLeft) = links.items()[0]
		while (linksLeft > 1) :
			# randomly remove a current link
			a = random.randint(0, len(g) - 1)
			while (a == node or len(g[a] - sets.Set([node])) == 0 or a in g[node]) :
				a = random.randint(0, len(g) - 1)
			b = random.choice(list(g[a]))
			while (b in g[node]) :
				b = random.choice(list(g[a]))
			g[a].remove(b)
			g[b].remove(a)
			# removed link is (a, l), add new links (node, a), (node, b)
			g[node].add(a)
			g[a].add(node)
			g[node].add(b)
			g[b].add(node)
			linksLeft = linksLeft - 2
	return g

n = int(sys.argv[1])
x = int(sys.argv[2])

g = genGraph(n, x)

for i in range(0, len(g)) :
	print str(list(g[i]))[1:-1]

