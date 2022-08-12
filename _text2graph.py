'''
For constraint error and related failing elements recorded in Text file
Convert to Data dictionary 
Used Data dictionary to create Node-Edge graph
'''

import networkx as nx
import pprint
from pyvis.network import Network
import json
from helper import *
import os


######################## Import Data Text File ############################

'''
Data text file format :
    ** List of Constraint Errors in Edge dictionary form
    ** Edge dictionary is used to created one node-edge-node connection
        - type/group name in string used for label 
        - uid in string used to retrive Id and element (if brought back to Revit)


    "[
        {
        "nodes":[(node1_uid, category),(node2_uid, category)], # refplane / faminstance / genericform / wall
        "subedges":[
                    (deflinstyle_uid, "Default Linear Style"), 
                    (line_uid, "Line"),
                    (alignment_uid1, "Alignment"), 

                    (host_uid, "Host"), (?)
                    (symline_uid1, "Symbolic Line"), (?)
                    (sketchplane_uid1, "Sketch Plane") (?)
                    ] # can have single or multiple
        },
        {...},
    ]"
'''

'''
Data dictionary format 
Data = {
		"node_cat"  :   ["ReferencePlane", "Wall", "Sweep", "Extrusion"] # list of Node types in string format
		"node_list" :   [...] # list of node in tuple format (node name, id)
		"edge_list" :   # list of Edge Dictionaries
                        [
                            {
                            "nodes":[(node1_uid, category),(node2_uid, category)], # refplane / faminstance / genericform / wall
                            "subedges":[
                                        (deflinstyle_uid, "Default Linear Style"), 
                                        (line_uid, "Line"),
                                        (alignment_uid1, "Alignment"), 

                                        (host_uid, "Host"), (?)
                                        (symline_uid1, "Symbolic Line"), (?)
                                        (sketchplane_uid1, "Sketch Plane") (?)
                                        ] # can have single or multiple
                            },
                            {...},
                        ]
    }

'''


## Data dictionary (will be exported to json file)
Data = dict()

## Get edge_list from edge_list text file
with open('edge_list_org.txt', 'r+') as org:

    # Delete last ,
    org_txt = org.read()
    lastcomma = org_txt.rfind(',')
    org_txt = org_txt[:lastcomma]

with open('edge_list.txt', 'w+') as mod:
    mod_txt = '{"edge_list" : [ \n' + org_txt + '\n ]}'
    mod.write(mod_txt)

edge_list = open('edge_list.txt').read()
Data = json.loads(edge_list) # Start Data dictionary with edge_list

## Get node_cat
node_cat = open('node_cat.txt').read()
Data['node_cat'] = json.loads(node_cat) # add to data

pprint.pprint(Data) # Data Dictionary!

######################## Create Graph from dictionary ############################
G = nx.MultiGraph()

for e in Data['edge_list']:
    subedges = e['subedges']
    nodes = e['nodes']
    if len(nodes) == 2: # only add node-edge-node connections (there are 1 node constraints)
        two_nodes = [] # To create edge
        for n in nodes:
            n_uid = n[0]
            n_id = n[1]
            n_cat = n[2]
            n_name = n_cat + ' ' + n_id
            two_nodes.append(n_name)
            G.add_node(n_name, group=n_cat, uid=n_uid) # add_node() merges duplicates!
        for se in subedges:
            se_uid = se[0]
            se_id = se[1]
            se_cat = se[2]
            se_name = se_cat + ' ' + se_id
            G.add_edge(*two_nodes, title=se_name, group=se_cat, uid=se_uid, color='black')


######################## Visualize with Pyvis ############################
#node_color = {'Reference Plane':'red', 'Sweep':'lime'}
nt = Network('900px', '900px')
nt.from_nx(G)# populates the nodes and edges data structures
# nt.show_buttons(filter_=['physics'])
# edge_labels = nx.get_edge_attributes(G,'name')
pos=nx.spring_layout(G)
# label and color code
# nx.draw_networkx_edge_labels(G, pos=pos, edge_labels = edge_labels)
nx.draw_networkx_edge_labels(G, pos=pos)
# edge_color = nx.get_edge_attributes(G, 'color')

nx.draw(G, pos=pos, with_labels=True)
nt.show_buttons()
nt.show('output.html')