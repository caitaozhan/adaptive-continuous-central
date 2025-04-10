"""
Program for drawing network from json file
input: relative path to json file
Graphviz library must be installed

NOTE: this file currently only works for sequential simulation files.
If your JSON file contains parallel simulation information, please remove before use.
"""

import argparse
from graphviz import Graph
from json import load
from collections import defaultdict

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from router_net_topo_adaptive import RouterNetTopoAdaptive
from sequence.topology.qkd_topo import QKDTopo


parser = argparse.ArgumentParser()
parser.add_argument('config_file', help="path to json file defining network")
parser.add_argument('-d', '--directory', type=str, default='tmp', help='directory to save the figure')
parser.add_argument('-f', '--filename', type=str, default='topology', help='filename of the figure')
parser.add_argument('-m', '--draw_middle', action='store_true')

args = parser.parse_args()
directory = args.directory
filename = args.filename
draw_middle = args.draw_middle

# determine type of network
with open(args.config_file, 'r') as fh:
    config = load(fh)
nodes = config["nodes"]
node_type = nodes[0]["type"]

if node_type == RouterNetTopoAdaptive.BSM_NODE or node_type == RouterNetTopoAdaptive.QUANTUM_ROUTER or node_type == RouterNetTopoAdaptive.CONTROLLER:
    topo = RouterNetTopoAdaptive(args.config_file)
elif node_type == QKDTopo.QKD_NODE:
    topo = QKDTopo(args.config_file)
else:
    raise Exception("Unknown node type '{}' in config file {}".format(node_type, args.config_file))

# make graph
g = Graph(format='png')
g.attr(layout='neato', overlap='false')

# add nodes and translate qchannels from graph
node_types = list(topo.nodes.keys())

for node_type in node_types:
    if node_type == RouterNetTopoAdaptive.BSM_NODE:
        if draw_middle:
            for node in topo.get_nodes_by_type(node_type):
                # g.node(node.name, label='BSM', shape='rectangle')  # simple label for BSM node
                g.node(node.name, shape='rectangle')
    elif node_type == RouterNetTopoAdaptive.QUANTUM_ROUTER:
        for node in topo.get_nodes_by_type(node_type):
            # g.node(node.name, label='', style='filled')
            g.node(node.name, style='filled')

if draw_middle:
    # draw the middle BSM node
    for qchannel in topo.get_qchannels():
        g.edge(qchannel.sender.name, qchannel.receiver, color='blue', dir='forward')
else:
    # do not draw the middle BSM node
    dist = {}
    bsm_to_node = defaultdict(list)
    for qchannel in topo.get_qchannels():
        node = qchannel.sender.name
        bsm = qchannel.receiver
        bsm_to_node[bsm].append(node)
        if len(bsm_to_node[bsm]) == 2:
            node1, node2 = bsm_to_node[bsm]
            dist[(node1, node2)] = round(qchannel.distance * 2)
    qconnections = set()
    for bsm, nodes in bsm_to_node.items():
        assert len(nodes) == 2, f'{bsm} connects to {len(nodes)} number of nodes (should be 2)'
        distance = str(dist[(nodes[0], nodes[1])])
        g.edge(nodes[0], nodes[1], color='blue', penwidth='2', label=distance)


g.view(directory=directory, filename=filename)


# python config/draw_topo.py config/mesh_6.json -d config -f mesh_6
# python config/draw_topo.py config/random_10.json -d config -f random_10