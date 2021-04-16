#! /usr/bin/env python

import sys
import pickle
import os.path


K = 64
linkRank_ECMP_64 = {}
linkRank_ECMP_8 = {}
linkRank_K = {}


"""
Add the links in these paths to the linkRanks for K shortest
"""
def k_links(paths):
    length = len(paths)
    p = paths
    # we only care about the 8 shortest
    if length > 8:
        p = paths[:8]
    links = set([item for sublist in p for item in sublist])
    for link in links:
        if link in linkRank_K:
            linkRank_K[link] = linkRank_K[link] + 1
        else:
            linkRank_K[link] = 1


"""
Add the links in these paths to the linkRanks for ECMP and
its appropriate way
"""
def ecmp_links(paths, way):
    length = len(paths)
    # we only care about either the first 8 or all 64
    if way == 8 and length > way:
        paths = paths[:way]
    # since this is ECMP, then only same lowest cost will be considered
    lowest_cost = len(paths[0])
    uniques = set([])
    for path in paths:
        if lowest_cost != len(path):
            return
        links = set(path).difference(uniques)
        for link in links:
            if way == 64:
                if link in linkRank_ECMP_64:
                    linkRank_ECMP_64[link] = linkRank_ECMP_64[link] + 1
                else:
                    linkRank_ECMP_64[link] = 1
            else:
                if link in linkRank_ECMP_8:
                    linkRank_ECMP_8[link] = linkRank_ECMP_8[link] + 1
                else:
                    linkRank_ECMP_8[link] = 1
        uniques = uniques.union(links)


"""
Although we're supposed to find the shortest paths, because the
weight is all 1's. Then it only becomes BFS. Takes in the
adjacency matrix and the source/target tuple list, outputs
a list of paths from shortest to longest
"""
def k_bfs(adj, A_B):
    (s, t) = A_B
    paths = []
    queue = []
    queue.append([s])
    if s == t:
        return None

    while queue:
        # get the first path from the queue
        path = queue.pop(0)
        # get the last node from the path
        node = path[-1]
        # path found, add it to the paths already and continue with the next one
        if node == t:
            linkPath = zip(path[:len(path) - 1], path[1:])
            paths.append(linkPath)

            # If there's enough paths already or none left, then return
            if len(paths) == K or (len(paths) == 8 and len(paths[-1]) != len(paths[0])):
                return paths
            continue
        # enumerate all adjacent nodes, construct a new path and push it into the queue
        if node in adj:
            for adjacent in adj[node]:
                if adjacent not in path :
                    new_path = list(path)
                    new_path.append(adjacent)
                    queue.append(new_path)
    return paths


"""
Create an adjacency matrix from the adjacency file
everything is comma, then space separated
"""
def file_to_graph(filename):
    adj = {}
    f = open(filename, 'r')
    i = 0
    for line in f:
        adj[i] = map(int, [x.strip() for x in line.split(',')])
        i += 1
    f.close()
    return adj


"""
Create a list of tuples of (source, destination) to
find paths for
"""
def file_to_tuple(filename):
    tup = []
    f = open(filename, 'r')
    for line in f:
        source_dest = map(int, [x.strip() for x in line.split(',')])
        tup.append((source_dest[0], source_dest[1]))
    f.close()
    return tup


def write_data(dest_file, servers, switches, ports):
    k_values = linkRank_K.values()
    k_values = sorted(k_values, reverse = True)
    ecmp_8_values = linkRank_ECMP_8.values()
    ecmp_8_values = sorted(ecmp_8_values, reverse = True)
    ecmp_64_values = linkRank_ECMP_64.values()
    ecmp_64_values = sorted(ecmp_64_values, reverse = True)

    i = 0
    len_K = len(k_values)
    len_e8 = len(ecmp_8_values)
    len_e64 = len(ecmp_64_values)

    total = switches * ports

    while i < total:
        rank = total - i
        k = 0
        if i < len_K:
            k = k_values[i]
        eight = 0
        if i < len_e8:
            eight = ecmp_8_values[i]
        sixtyfour = 0
        if i < len_e64:
            sixtyfour = ecmp_64_values[i]
        print str(rank) + "\t" + str(k) + "\t" + str(eight) + "\t" + str(sixtyfour)
        i += 1

    if os.path.isfile(dest_file):
        dest_output = open(dest_file, "a")
    else:
        dest_output = open(dest_file, "w")

    servers_per_switch = float(servers) / switches

    dest_output.write(str(servers_per_switch) + "\t" + str(min(k_values)) + "\t" + str(max(k_values)) + "\t" + str(float(sum(k_values))/len(k_values)) + "\n")
    dest_output.close()


if __name__=='__main__':
    
    dest_file = sys.argv[3]

    # read adjacency and source/target nodes files
    adj = file_to_graph(sys.argv[1])
    source_dest = file_to_tuple(sys.argv[2])

    i = 0
    # for each source and target, find the 64 shortest paths
    for A_B in source_dest:
        i+= 1
        paths = k_bfs(adj, A_B)
        # for each path, add the links towards the ranklink counts
        if paths:
            k_links(paths)
            ecmp_links(paths, 8)
            ecmp_links(paths, 64)

    write_data(dest_file, int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
