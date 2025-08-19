import random
import networkx as nx
import pandas as pd


shift=1000

def load():
    max_students = 2
    meaningful_pref = 2
    min_day = 2
    presources = -1
    pagents = -1
    return load_one_student_per_room(max_students, meaningful_pref, min_day, presources, pagents)

def generate_values(cost, pref_attr, resource_attr):
    attributes_r = set()
    attributes_p = set()
    for item in resource_attr.values():
        for key in item.keys():
            attributes_r.add(key)
    for item in pref_attr.values():
        for key in item.keys():
            attributes_p.add(key)
    resource_attr_small = {}
    for k, v in resource_attr.items():
        resource_attr_small[k] = {}
        for k2, v2 in v.items():
            if k2 in attributes_p:
                resource_attr_small[k][k2] = v2

    values = {}
    opp_values = {}

    for k, v in cost.items():
        values[k] = {}
        opp_values[k] = {}
        for attr in v.keys():
            mx = max(v[attr].values())
            values[k][(attr, 0)] = 0
            values[k][(attr, 1)] = mx
            values[k][(attr, 0.5)] = mx / 2

            opp_values[k][(attr, 0)] = (attr, 0)
            opp_values[k][(attr, mx)] = (attr, 1)

            for i in range(1, mx):
                opp_values[k][(attr, i)] = (attr, 0.5)
    return pref_attr, resource_attr_small, values, opp_values


def load_one_student_per_room(max_students, meaningful_pref, min_day, presources=-1, pagents=-1):
    apply_alone = False
    prefix = "datasets/students/"
    preferencesp = prefix + "student_preferences.csv"
    roomsp = prefix + "lab_rooms.csv"
    advisorsp = prefix + "student_details.csv"

    df_prefs = pd.read_csv(preferencesp)
    df_rooms = pd.read_csv(roomsp)
    df_advisors = pd.read_csv(advisorsp)

    prefs = df_prefs.to_dict()
    rooms = df_rooms.to_dict()
    advisors = df_advisors.to_dict()

    G = nx.Graph()

    left = set()
    right = set()

    for c, pid in enumerate(prefs['id']):
        if random.random() < pagents or pagents < 0:
            left.add((c, pid))
            G.add_node(pid, bipartite=0)

    for r, rid in rooms['id'].items():
        if random.random() < presources or presources < 0:
            right.add((r, rid + shift))
            G.add_node(rid + shift, bipartite=1)

    for j in range(1, max_students):
        for r, rid in rooms['id'].items():
            if rooms['size'][r] == 2 and rooms['seats'][r] > j:
                if random.random() < presources or presources < 0:
                    right.add((r, rid + (1 + j) * shift))
                    G.add_node(rid + (1 + j) * shift, bipartite=1)

    fields = set()
    resource_attr = {}
    pref_attr = {}
    for rid in right:
        resource_attr[rid[1]] = {}
        for field in rooms:
            if field != 'id':
                resource_attr[rid[1]][field] = rooms[field][rid[0]]
                fields.add(field)

    cost = {}
    final_fields = set()
    days = {}
    for pid in left:

        cost[pid[1]] = {}
        pref_attr[pid[1]] = {}

        advisor = None
        near = None
        specific = False
        sp_number = None
        sp_level = None
        alone_level = None

        for field in prefs:
            if field in fields:
                final_fields.add(field)
                cost[pid[1]][field] = {}
                pref_attr[pid[1]][field] = {}

                for rrid, rid in rooms['id'].items():

                    cost[pid[1]][field][rid + shift] = 0 if rooms[field][rrid] > 0 else max(
                        prefs[field][pid[0]] - meaningful_pref + 1, 0)  # if want, price for relaxation will be high
                    pref_attr[pid[1]][field] = 0 if max(prefs[field][pid[0]] - meaningful_pref + 1, 0) == 0 else 1
                    if (rid + shift) not in resource_attr:
                        resource_attr[rid + shift] = {}
                    if field not in resource_attr[rid + shift]:
                        resource_attr[rid + shift][field] = {}
                    resource_attr[rid + shift][field] = 0 if rooms[field][rrid] == 0 else 1

                    for j in range(1, max_students):
                        if (rid + ((1 + j) * shift)) in G.nodes():
                            if (rid + ((1 + j) * shift)) not in resource_attr:
                                resource_attr[(rid + ((1 + j) * shift))] = {}
                            cost[pid[1]][field][(rid + ((1 + j) * shift))] = cost[pid[1]][field][rid + shift]

                            resource_attr[(rid + ((1 + j) * shift))][field] = resource_attr[rid + shift][field]

            advisor = advisors['advisor'][pid[0]]

            if field == 'near_advisor':
                near = prefs[field][pid[0]]

            if field == 'specific_room':
                specific = True if prefs[field][pid[0]] > 0 else False

            if field == 'specific_room_number':
                sp_number = prefs[field][pid[0]]

            if field == 'specific_room_importance':
                sp_level = prefs[field][pid[0]]

            if field == 'alone':
                alone_level = prefs[field][pid[0]]

            if field == 'silent':
                silent_level = prefs[field][pid[0]]

        field = None

        if advisor == 1:
            field0 = 'distance_to_advisor0'
            field1 = 'distance_to_advisor1'
            adv0 = "advisor0"
            adv1 = "advisor1"

        elif advisor == 2:
            field0 = 'distance_to_advisor1'
            field1 = 'distance_to_advisor0'
            adv0 = "advisor1"
            adv1 = "advisor0"

        cost[pid[1]][adv0] = {}
        for rrid, rid in rooms['id'].items():
            cost[pid[1]][adv0][rid + shift] = 0 if rooms[field0][rrid] > 0 else max(near - meaningful_pref + 1,
                                                                                    0)  # if want, price for relaxation will be high
            pref_attr[pid[1]][adv0] = 0 if max(near - meaningful_pref + 1, 0) == 0 else 1
            resource_attr[rid + shift][adv0] = 0 if rooms[field0][rrid] == 0 else 1
            for j in range(1, max_students):
                if (rid + ((1 + j) * shift)) in G.nodes():
                    cost[pid[1]][adv0][(rid + ((1 + j) * shift))] = cost[pid[1]][adv0][rid + shift]
                    resource_attr[(rid + ((1 + j) * shift))][adv0] = resource_attr[rid + shift][adv0]

        cost[pid[1]][adv1] = {}
        for rrid, rid in rooms['id'].items():
            cost[pid[1]][adv1][rid + shift] = 0
            pref_attr[pid[1]][adv1] = 0
            resource_attr[rid + shift][adv1] = 0 if rooms[field1][rrid] == 0 else 1
            for j in range(1, max_students):
                if (rid + ((1 + j) * shift)) in G.nodes():
                    cost[pid[1]][adv1][(rid + ((1 + j) * shift))] = cost[pid[1]][adv1][rid + shift]
                    resource_attr[(rid + ((1 + j) * shift))][adv1] = resource_attr[rid + shift][adv1]

        if specific:
            cost[pid[1]]['specific'] = {}
            field = 'id'
            for rrid, rid in rooms['id'].items():
                cost[pid[1]]['specific'][rid + shift] = 0 if rooms[field][rrid] == sp_number else max(
                    sp_level - meaningful_pref + 1, 0)  # if want, price for relaxation will be high
                pref_attr[pid[1]]['specific'] = 0 if max(sp_level - meaningful_pref + 1,
                                                         0) == 0 else 1  # if want, price for relaxation will be high
                resource_attr[rid + shift]['specific'] = 1
                for j in range(1, max_students):
                    if (rid + ((1 + j) * shift)) in G.nodes():
                        cost[pid[1]]['specific'][(rid + ((1 + j) * shift))] = cost[pid[1]]['specific'][rid + shift]
                        resource_attr[(rid + ((1 + j) * shift))]['specific'] = resource_attr[rid + shift]['specific']
        else:
            cost[pid[1]]['specific'] = {}
            field = 'id'
            for rrid, rid in rooms['id'].items():
                cost[pid[1]]['specific'][rid + shift] = 0
                pref_attr[pid[1]]['specific'] = 0
                resource_attr[rid + shift]['specific'] = 1  # all rooms can be specific
                for j in range(1, max_students):
                    if (rid + ((1 + j) * shift)) in G.nodes():
                        cost[pid[1]]['specific'][(rid + ((1 + j) * shift))] = cost[pid[1]]['specific'][rid + shift]
                        resource_attr[rid + shift]['specific'] = resource_attr[rid + shift]['specific']

        if apply_alone and alone_level is not None:
            cost[pid[1]]['alone'] = {}
            field = 'seats'
            for rrid, rid in rooms['id'].items():
                cost[pid[1]]['alone'][rid + shift] = 0 if rooms[field][rrid] == 1 else max(
                    alone_level - meaningful_pref + 1, 0)  # if want, price for relaxation will be high
                pref_attr[pid[1]]['alone'] = 0 if max(alone_level - meaningful_pref + 1, 0) == 0 else 1
                resource_attr[rid + shift]['alone'] = 1 if rooms[field][rrid] == 1 else 0

                for j in range(1, max_students):
                    if (rid + ((1 + j) * shift)) in G.nodes():
                        cost[pid[1]]['alone'][(rid + ((1 + j) * shift))] = cost[pid[1]]['alone'][rid + shift]
                        resource_attr[(rid + ((1 + j) * shift))]['alone'] = resource_attr[rid + shift]['alone']

        if silent_level is not None:
            cost[pid[1]]['silent'] = {}
            field = 'distance_to_kitchen'
            for rrid, rid in rooms['id'].items():
                cost[pid[1]]['silent'][rid + shift] = 0 if rooms[field][rrid] == 0 else max(
                    silent_level - meaningful_pref + 1, 0)  # if want, price for relaxation will be high
                pref_attr[pid[1]]['silent'] = 0 if max(alone_level - meaningful_pref + 1, 0) == 0 else 1
                resource_attr[rid + shift]['silent'] = 0 if rooms[field][rrid] == 0 else 1
                for j in range(1, max_students):
                    if (rid + ((1 + j) * shift)) in G.nodes():
                        cost[pid[1]]['silent'][(rid + ((1 + j) * shift))] = cost[pid[1]]['silent'][rid + shift]
                        resource_attr[(rid + ((1 + j) * shift))]['silent'] = resource_attr[rid + shift]['silent']

        else:
            cost[pid[1]]['silent'] = {}
            for rrid, rid in rooms['id'].items():
                cost[pid[1]]['silent'][rid + shift] = 0
                pref_attr[pid[1]]['silent'] = 0
                for j in range(1, max_students):
                    if (rid + ((1 + j) * shift)) in G.nodes():
                        cost[pid[1]]['silent'][(rid + ((1 + j) * shift))] = cost[pid[1]]['silent'][rid + shift]

    pool = {}

    for pid in cost:
        restricted = set()
        all_rooms = set()

        for fname, field in cost[pid].items():

            for room in field.items():
                all_rooms.add(room[0])
                if room[1] > 0:
                    restricted.add(room[0])

        ls = tuple(sorted(list(all_rooms - restricted)))
        if ls not in pool:
            pool[ls] = [pid]
        else:
            pool[ls].append(pid)

        for room_id in all_rooms - restricted:
            if room_id in G.nodes():
                G.add_edge(pid, room_id)

    attributes = set()
    for item in cost.items():
        break
    for item in cost.values():
        for key in item:
            attributes.add(key)

    pref_attr, resource_attr, values, opp_values = generate_values(cost, pref_attr, resource_attr)

    return G, len(left), len(right), resource_attr, pref_attr, values, opp_values
