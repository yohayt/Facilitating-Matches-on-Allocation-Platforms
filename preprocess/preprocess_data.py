import copy

import preprocess.prepare_data_children as prepare_data_children
import preprocess.prepare_data_courses as prepare_data_courses
import preprocess.prepare_data_students as prepare_data_students
import networkx as nx
import util
from preprocess import prepare_data_children_many, prepare_data_courses_many


# code for preprocessing the data. Uses different classes for the different datasets.
def process(dataset):
    if dataset == "courses" or dataset == "COURSE":
        gr, n, m, resource_attr, pref_attr, values = prepare_data_courses.load()

        opp_values = {}

        for person_id in values:
            opp_values[person_id] = {}
            for pair in values[person_id]:
                opp_values[person_id][(pair[0], values[person_id][pair])] = pair
        top_nodes = add_missing_edges(gr, pref_attr, resource_attr, values)
        porder = {"capacity_max": 0, "capacity_min": 1, "region": 2, "hearing": 3, "table": 4}
        print(gr,n,m)
    elif dataset == "students" or dataset == 'LAB':
        gr, n, m, resource_attr, pref_attr, values, opp_values = prepare_data_students.load()
        top_nodes = add_missing_edges(gr, pref_attr, resource_attr, values)
        porder = {'wifi': 0, 'cabinet': 1, 'advisor0': 2, 'advisor1': 3, 'specific': 4, 'silent': 5}

    elif dataset == "children" or dataset == 'CHILD':
        gr, n, m, resource_attr, pref_attr, values, opp_values = prepare_data_children.load()
        top_nodes = add_missing_edges_children(gr, pref_attr, resource_attr, values)
        porder = {"max_age": 0, "min_age": 1, "pref": 2}

    elif dataset == "mcld":
        gr, n, m, resource_attr, pref_attr, values, opp_values = prepare_data_children_many.load()
        top_nodes = add_missing_edges_children(gr, pref_attr, resource_attr, values)
        porder = {"max_age": 0, "min_age": 1, "pref": 2}
    elif dataset == "course_many":
        gr, n, m, resource_attr, pref_attr, values = prepare_data_courses_many.load()
        opp_values = {}

        for person_id in values:
            opp_values[person_id] = {}
            for pair in values[person_id]:
                opp_values[person_id][(pair[0], values[person_id][pair])] = pair
        top_nodes = add_missing_edges(gr, pref_attr, resource_attr, values)
        porder = {"capacity_max": 0, "capacity_min": 1, "region": 2, "hearing": 3, "table": 4}
        print(gr,n,m)

    nx.set_edge_attributes(gr, values=1 + len(top_nodes), name='weight')# the weights of orignal edges
    nx.set_edge_attributes(gr, values=0, name='cost')# the other weights are defined later

    gr2 = copy.deepcopy(gr)
    nx.set_edge_attributes(gr2, values=(1 + len(top_nodes))**2, name='weight') # the weights of orignal edges
    nx.set_edge_attributes(gr2, values=0, name='cost')

    gr3 = copy.deepcopy(gr)
    nx.set_edge_attributes(gr3, values=1 + len(top_nodes), name='weight')  # the weights of orignal edges
    nx.set_edge_attributes(gr3, values=0, name='cost')

    return gr, gr2, gr3, n, m, resource_attr, pref_attr, values, opp_values, porder


def add_missing_edges(gr, pref_attr, resource_attr, values):
    top_nodes = {n for n, d in gr.nodes(data=True) if d["bipartite"] == 0}
    for node in top_nodes:
        resources = resource_attr.keys()
        for i in resources:
            if util.satisfied_thresh(values, node, resource_attr[i], pref_attr[node]):
                gr.add_edge(node, i)
    return top_nodes


def add_missing_edges_children(gr, pref_attr, resource_attr, values):
    top_nodes = {n for n, d in gr.nodes(data=True) if d["bipartite"] == 0}
    for node in top_nodes:
        resource_attr_sm = resource_attr[node]
        resources = resource_attr_sm.keys()
        for i in resources:
            if util.satisfied_thresh(values, node, resource_attr_sm[i], pref_attr[node]):
                gr.add_edge(node, i)
    return top_nodes
