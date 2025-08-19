import os
import random
import networkx as nx
import csv


def load():
    prefix = 'datasets/courses/'
    #prefix = '../datasets/courses/'
    courses = prefix + "courses.csv"
    rooms = prefix + "rooms.csv"
    order_of_regions = prefix + "order_of_regions.csv"
    course = {}
    room = {}
    all_regions = set()

    with open(courses, "r") as f_courses, \
            open(rooms, "r") as f_rooms:

        first = True
        reader = csv.reader(f_courses, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        for c in reader:
            sp = c
            if first:
                first = False
                continue
            try:
                course[sp[0]] = {'course_id': sp[1], 'planned_registered_students': int(sp[2]),
                                 'prefered_region': int(sp[3])}

                addition = random.randint(0,2)
                if addition >0:
                    for i in range(addition):
                        course[str(int(sp[0])+i*1000000)] = {'course_id': str(int(sp[1]) + i*1000000), 'planned_registered_students': int(sp[2]),
                                 'prefered_region': int(sp[3])}
            except Exception as e:
                print("ERROR IN LINE {}".format(sp))
                raise e

        first = True
        reader = csv.reader(f_rooms, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        for r in reader:
            if random.random() > 0.1:
                #                        if True:

                sp = r
                if first:
                    first = False
                    continue
                try:
                    room[sp[0]] = {'region': int(sp[1]), 'building': int(sp[2]), 'room': int(sp[3]),
                                   'capacity': int(sp[4]), 'accessories': sp[5].split(",") if sp[5] != 'NULL' else []}
                    all_regions.add(int(sp[1]))
                except Exception as e:
                    print("ERROR IN LINE {}".format(sp))
                    raise e
            else:
                try:
                    sp = r
                    all_regions.add(int(sp[1]))
                except:
                    continue
    edges = []

    resource_attr = {}
    pref_attr = {}

    all_disabilities = ['hearing_dis_sys', 'accecible_table']

    for c in course:

        cap = course[c]['planned_registered_students']

        if cap == 0:
            continue

        if c not in pref_attr:
            pref_attr[c] = {}

        pref_attr[c]['hearing'] = 0
        pref_attr[c]['table'] = 0

        if random.random() > 0.9:
            if 'hearing_dis_sys' in random.choice(all_disabilities):
                pref_attr[c]['hearing'] = 1
            else:
                pref_attr[c]['table'] = 1
            if random.random() > 0.9:
                pref_attr[c]['hearing'] = 1
                pref_attr[c]['table'] = 1
        cap = course[c]['planned_registered_students']

        if c not in pref_attr:
            pref_attr[c] = {}

        pref_attr[c]['capacity_min'] = int(cap / 10) * 10
        pref_attr[c]['capacity_max'] = min(int(int((4 / 3 * cap) / 10) * 10), 270)

        pref_attr[c]['region'] = course[c]['prefered_region']
        if pref_attr[c]['region'] < 0:
            pref_attr[c]['region'] = 2000

    for r in room:
        cap = room[r]['capacity']
        if (10000000 + int(r)) not in resource_attr:
            resource_attr[10000000 + int(r)] = {}

        resource_attr[10000000 + int(r)]['capacity_min'] = int(cap / 10) * 10
        resource_attr[10000000 + int(r)]['capacity_max'] = int(cap / 10) * 10
        resource_attr[10000000 + int(r)]['region'] = room[r]['region']
        resource_attr[10000000 + int(r)]['hearing'] = 1 if 'hearing_dis_sys' in room[r]['accessories'] else 0
        resource_attr[10000000 + int(r)]['table'] = 1 if 'accecible_table' in room[r]['accessories'] else 0

    G = nx.Graph()
    for edge in edges:
        first_node = edge[0]
        last_node = edge[1]
        G.add_node(first_node, bipartite=0)
        G.add_node(last_node, bipartite=1)
        G.add_edge(first_node, last_node)

    for c in pref_attr:
        G.add_node(c, bipartite=0)

    for r in resource_attr:
        G.add_node(r, bipartite=1)

    n_nodes = {n for n, d in G.nodes(data=True) if d["bipartite"] == 0}
    n = len(n_nodes)
    m = len(set(G) - n_nodes)
    values = {}

    regions_set = set()
    for resource in resource_attr:
        regions_set.add(resource_attr[resource]['region'])

    for c in pref_attr:
        if pref_attr[c]['region'] == 2000:
            pref_attr[c]['region'] = random.choice(list(regions_set))

    regions_order = {}
    with open(order_of_regions, "r") as f:
        for line in f:
            sp = line.strip().split(":")
            regions_order[int(sp[0])] = []
            for item in sp[1].strip().split(","):
                regions_order[int(sp[0])].append(int(item))

    for c in course:
        if c not in pref_attr:
            continue

        values[c] = {}

        i = 0
        for i in range(0, 280, 10):
            values[c][('capacity_min', i)] = i / 10
        j = 0
        for i in range(270, -1, -10):
            values[c][('capacity_max', i)] = j
            j += 1

        if pref_attr[c]['region'] in regions_order:
            res_order = list(regions_order[pref_attr[c]['region']])
        else:
            regions_set = all_regions
            res_order = list(regions_set)
            random.shuffle(res_order)

        ln = len(res_order)

        for i, v in enumerate(res_order):
            values[c][('region', v)] = ln - i - 1

        values[c][('hearing', 0)] = 0
        values[c][('hearing', 1)] = 1
        values[c][('table', 0)] = 0
        values[c][('table', 1)] = 1

    return G, n, m, resource_attr, pref_attr, values
