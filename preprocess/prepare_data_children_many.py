import copy
import random

import networkx as nx
import datetime



def load():
    prefix = "datasets/children/"
    #prefix = "../datasets/children/"
    period = prefix + 'period.csv'
    occurrence = prefix + 'occurrence.csv'
    lifetime = prefix + 'lifetime.csv'
    knome = prefix + 'knome.csv'
    child = prefix + 'child.csv'
    activity = prefix + 'activity.csv'
    preference = prefix + 'preference.csv'

    preflimit = {'1'}
    all_prefs = {'1', '2', '3', '4'}

    children = {}
    preferences = {}
    activities = {}
    lifetime_child_to_oc = {}
    lifetime_oc_to_child = {}
    occurrences = {}
    periods = {}

    with open(preference, "r") as f_pref, open(activity, "r") as f_activity, \
            open(child, "r") as f_child, open(knome, "r") as f_knome, open(lifetime, "r")  as f_lifetime, \
            open(occurrence, "r") as f_occurrence, open(period, "r") as f_period:

        first = True
        for pref in f_pref:
            sp = pref.strip().split(',')
            if first:
                first = False
                continue

            if sp[2] in all_prefs:
                if sp[3] not in preferences:
                    preferences[sp[3]] = {}

                if sp[2] not in preferences[sp[3]]:
                    preferences[sp[3]][sp[2]] = []
                preferences[sp[3]][sp[2]].append(sp[1])

        first = True
        for act in f_activity:
            sp = act.strip().split(',')
            if first:
                first = False
                continue
            activities[sp[0]] = {'life': sp[3], 'min_child': int(sp[4]) if len(sp[4]) > 0 else 0,
                                 'max_child': int(sp[5]) if len(sp[5]) > 0 else 1000,
                                 'min_age': int(sp[6]) if len(sp[6]) > 0 else 0,
                                 'max_age': int(sp[7]) if len(sp[7]) > 0 else 1000, 'similarity': sp[8]}

        first = True
        for ch in f_child:
            instances = random.randint(1, 3)

            if first:
                first = False
                continue

            children[ch.strip().split(",")[1]] = datetime.datetime.strptime(ch.strip().split(",")[0], '%Y-%m-%d')

        first = True
        for lt in f_lifetime:
            if first:
                first = False
                continue
            sp = lt.strip().split(",")
            if sp[0] not in lifetime_oc_to_child:
                lifetime_oc_to_child[sp[0]] = set()
            lifetime_oc_to_child[sp[0]].add(sp[1])

            if sp[1] not in lifetime_child_to_oc:
                lifetime_child_to_oc[sp[1]] = set()
            lifetime_child_to_oc[sp[1]].add(sp[0])

        first = True
        for occ in f_occurrence:
            if first:
                first = False
                continue

            sp = occ.strip().split(",")
            try:
                occurrences[sp[0]] = {'activity': sp[1],
                                      'start': datetime.datetime.strptime(sp[2], '%Y-%m-%d %H:%M:%S'), \
                                      'end': datetime.datetime.strptime(sp[3], '%Y-%m-%d %H:%M:%S'),
                                      'inactive': sp[4].lower() == "true", \
                                      'next': sp[5], 'prev': sp[6]}
            except:
                pass

        first = True
        for per in f_period:
            if first:
                first = False
                continue

            sp = per.strip().split(",")
            try:
                periods[int(sp[0])] = {'start': datetime.datetime.strptime(sp[1][1:-1], '%Y-%m-%d %H:%M:%S'), \
                                       'end': datetime.datetime.strptime(sp[2][1:-1], '%Y-%m-%d %H:%M:%S'),
                                       'max_assigned': int(sp[3])}
            except Exception as e:
                raise e
                pass

    edges = []

    relevant_periods = {52}

    dropped_period = 0
    dropped_age = 0
    dropped_lifetime = 0
    dropped_inactive = 0
    dropped_preference = 0


    resource_attr = {}
    pref_attr = {}
    values = {}
    opp_values = {}
    mn_age = 1000
    mx_age = 0

    k= 3


    occurences2 = {}
    first = True

    for occurrence in occurrences:
        if first:
            first = False
            continue
        instances = random.randint(1, 3)
        for instance in range(instances):
            occurrence_id = int(occurrence) + 10000000 * (instance + 1)
            occurences2[occurrence_id] = copy.deepcopy(occurrences[occurrence])
            occurences2[occurrence_id]['oid'] = occurrence

    for child in children:

        pref_attr[child] = {}
        resource_attr[child] = {}
        values[child] = {}
        opp_values[child] = {}

        for occurrence in occurences2:
                cont = False
                for period in relevant_periods:
                    if occurences2[occurrence]['start'] >= periods[period]['start'] and occurences2[occurrence]['end'] <= \
                            periods[period]['end']:
                        cont = True
                if not cont:
                    dropped_period += 1
                    continue

                if occurrence not in resource_attr[child]:
                    resource_attr[child][occurrence] = {}

                pref_attr[child] = {}

                birthday = children[child]
                start = occurences2[occurrence]['start']
                age = start.year - birthday.year - ((start.month, start.day) < (birthday.month, birthday.day))
                activity = occurences2[occurrence]['activity']

                pref_attr[child]['min_age'] = age
                pref_attr[child]['max_age'] = age

                resource_attr[child][occurrence]['min_age'] = activities[activity]['min_age']
                resource_attr[child][occurrence]['max_age'] = activities[activity]['max_age']

                child_in_preferences = child in preferences
                preference = 5
                occ = occurences2[occurrence]['oid']
                if child_in_preferences:
                    for item in all_prefs:
                        if item in preferences[child]:
                            if occ in preferences[child][item]:
                                preference = item

                pref_attr[child]['pref'] = 1
                resource_attr[child][occurrence]['pref'] = int(preference)

                j = 0
                for i in range(5, -1, -1):
                    values[child][('pref', i)] = j
                    opp_values[child][('pref', j)] = ('pref', i)
                    j += 1

                mn_age = min(mn_age, age, activities[activity]['min_age'])
                mx_age = max(mx_age, age, activities[activity]['max_age'])

                if age < activities[activity]['min_age'] or age > activities[activity]['max_age']:
                    dropped_age += 1
                    continue

                else:  # check lifetime
                    if (activities[activity]['life'] and child in lifetime_child_to_oc):
                        occ = lifetime_child_to_oc[child]
                        voided = False
                        for oc in occ:
                            if oc == activity:
                                voided = True
                        if voided:
                            dropped_lifetime += 1
                            continue

                    child_in_preferences = child in preferences
                    allowed_pref = False
                    if child_in_preferences:
                        for item in preflimit:
                            if item in preferences[child]:
                                if occ in preferences[child][item]:
                                    allowed_pref = True
                    if allowed_pref:  # check preferences...
                        if occurences2[occurrence]['inactive']:
                            dropped_inactive += 1
                            continue
                        edges.append((child, occurrence))
                    else:
                        dropped_preference += 1
                        continue

    for i in range(0, mx_age + 1):
        for child in children:
            values[child][('max_age', i)] = i
            opp_values[child][('max_age', i)] = ('max_age', i)

    j = 0
    for i in range(mx_age, -1, -1):
        for child in children:
            values[child][('min_age', i)] = j
            opp_values[child][('min_age', j)] = ('min_age', i)
        j += 1

    G = nx.Graph()
    for edge in edges:
        first_node = edge[0]
        last_node = edge[1]
        G.add_node(first_node, bipartite=0)
        G.add_node(last_node, bipartite=1)
        G.add_edge(first_node, last_node)

    for c in pref_attr:
        G.add_node(c, bipartite=0)

    for c in resource_attr:
        for r in resource_attr[c]:
            G.add_node(r, bipartite=1)

    n_nodes = {n for n, d in G.nodes(data=True) if d["bipartite"] == 0}
    n = len(n_nodes)
    m = len(set(G) - n_nodes)

    keys = list(resource_attr.keys())
    for item in keys:
        if resource_attr[item] == {}:
            del resource_attr[item]

    print(n,m)
    print(G)
    return G, n, m, resource_attr, pref_attr, values, opp_values
