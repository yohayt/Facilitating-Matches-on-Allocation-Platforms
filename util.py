import copy
import itertools
import random
import networkx as nx


def matching_size(agents, matching):  # calculate size of a matching
    matching_dict = dict(matching)

    ret = set()
    for x, y in matching_dict.items():
        if x in agents:
            ret.add(x)
        else:
            ret.add(y)
    return len(ret)


def partitions(n, I=1):  # an internal function of get_alpha_partitions()
    yield (n,)
    for i in range(I, n // 2 + 1):
        for p in partitions(n - i, i):
            yield (i,) + p


def get_alpha_partitions(n, i):  # all options to partition n items into i beans: how many options are there to relax with some cost bound?
    permutations = set()
    for item in partitions(n):
        item = [x for x in item]
        while len(item) < i:
            item.append(0)
        for item in itertools.permutations(item):
            if len(item) <= i:
                permutations.add(item)

    return permutations


def satisfied_thresh(values, person_id, resource_const, person_pref):  # check if an edge is relaxable
    for item1 in person_pref:
        try:
            if values[person_id][(item1, person_pref[item1])] > values[person_id][(item1, resource_const[item1])]:
                return False
        except Exception as e:
            print(resource_const[item1])
            raise e
    return True


def cost_consumed(values, person_id, resource_const, person_pref):  # returns the required cost for relaxing an edge
    consumed = 0

    for item1 in person_pref:
        try:
            consumed += max(
                values[person_id][(item1, person_pref[item1])] - values[person_id][(item1, resource_const[item1])], 0)
        except Exception as e:
            raise e
    return consumed


def calc_max_weight(agents, resources, weight, threshold_cost):  # calculate maximum values for discomfort functions
    # In combined functions, multiply by a factor for avoiding divisions.
    if weight == 0: #n agents.
        return 1
    elif weight == 1:
        return threshold_cost
    elif weight == 2:  # leximin
        return int((agents * resources + 1) ** threshold_cost)
    elif weight == 3:  # cost then leximin
        return int((threshold_cost * (agents * resources + 1) + 1)) * int((agents * resources + 1) ** threshold_cost)
    elif weight == 4:  # agent then leximin
        return int(((agents * resources + 1) + 1)) * int((agents * resources + 1) ** threshold_cost)
    elif weight == 5:  # lexi then cost
        return (int((agents * resources + 1) ** threshold_cost) * (agents * resources + 1) + 1) * threshold_cost
    elif weight == 6:  # agent then cost
        return int((agents * resources + 1) + 1) * int(threshold_cost)
    elif weight == 7:  # lexi then agent
        return int((agents * resources + 1) ** threshold_cost) * (agents * resources + 1) + 1
    elif weight == 8:  # cost then agent
        return int((threshold_cost * (agents * resources + 1) + 1))


#relax all edges with the m-cfair guarantee weights
def relax_with_bound_mcfair(g, resource_attr_1, pref_attr_1, budge, agents, values, opp_values, porder, weight, threshold):
    resource_attr = copy.deepcopy(resource_attr_1)
    agentst = list(agents)

    if 'min_age' in porder.keys():
        for item in agents:
            person_id = item
            break
        resource_attrp = resource_attr[person_id]
    else:
        resource_attrp = resource_attr

    mx = len(resource_attrp.keys()) #the maximum number of agents that we should add is at most the number of
                                            #resources

    mx_th = len(agents) + 1

    # code for adding dummy agents.
    gr = g.copy()
    for i in range(mx):

        agent = "***_{}".format(i)
        gr.add_node(agent, bipartite=0)

        agentst.append(agent)
        for resource in resource_attrp.keys():
            gr.add_edge(agent, resource, weight=mx_th, cost=0)  #beware- here we used the original weight

        g_alt, relaxed_resources = relax_all_mcfair(gr, resource_attr_1, pref_attr_1, budge, agents, values, opp_values,
                                                    porder, weight)

        matching = nx.max_weight_matching(g_alt)
        counter = 0
        relaxed_counter = 0
        for edge in matching:
            if (not isinstance(edge[0],int ) and "***" in edge[0]) or \
                    (not isinstance(edge[1],int ) and "***" in edge[1]):
                continue
            else:
                if g_alt[edge[0]][edge[1]]['cost']>0:
                    relaxed_counter += 1
                counter+=1

        if relaxed_counter<= threshold:
            return counter

#relax all edges with the p-cfair and f-cfair guarantee weights
def relax_with_bound(g, resource_attr_1, pref_attr_1, budge, agents, values, opp_values, porder, weight, threshold):
    resource_attr = copy.deepcopy(resource_attr_1)
    agentst = list(agents)

    if 'min_age' in porder.keys():
        for item in agents:
            person_id = item
            break
        resource_attrp = resource_attr[person_id]
    else:
        resource_attrp = resource_attr

    mx = len(resource_attrp.keys()) #the maximum number of agents that we should add is at most the number of
                                            #resources
    mx_th = len(agents) + 1

    # code for adding dummy agents.
    gr = g.copy()
    for i in range(mx):

        agent = "***_{}".format(i)
        gr.add_node(agent)
        agentst.append(agent)
        for resource in resource_attrp.keys():
            gr.add_edge(agent, resource, weight=mx_th, cost=0)  #beware- here we used the original weight

        g_alt, relaxed_resources = relax_all(gr, resource_attr_1, pref_attr_1, budge, agents, values, opp_values,
                                                 porder, weight)

        matching = nx.max_weight_matching(g_alt)
        counter = 0
        relaxed_counter = 0
        for edge in matching:
            if (not isinstance(edge[0],int ) and "***" in edge[0]) or \
                    (not isinstance(edge[1],int ) and "***" in edge[1]):
                continue
            else:
                if g_alt[edge[0]][edge[1]]['cost']>0:
                    relaxed_counter += 1
                counter+=1

        if relaxed_counter<= threshold:
            return counter

#relax all relaxable edges for the m-cfair weights
def relax_all_mcfair(g, resource_attr_1, pref_attr_1, budge, agents, values, opp_values, porder, weight):
    participate = set(participate_in_all_matchings(g))
    # this function adds all edges with cost<\infty to the graph.
    import copy

    resource_attr = copy.deepcopy(resource_attr_1)
    pref_attr = copy.deepcopy(pref_attr_1)
    values = copy.deepcopy(values)
    opp_values = copy.deepcopy(opp_values)
    gr = g.copy()

    if 'min_age' in porder.keys():
        for item in agents:
            person_id = item
            break
        resource_attrp = resource_attr[person_id]
    else:
        resource_attrp = resource_attr

    lagents = len(agents)
    lresources = len(resource_attrp.keys())

    max_weight = calc_max_weight(len(agents), len(resource_attrp.keys()), weight, budge)

    counter = 0
    import copy

    partitions = get_alpha_partitions(budge, len(porder.keys()))

    p_c = 0
    g_alt = copy.deepcopy(gr)
    for edge in g_alt.edges(data=True):
        edge[2]['weight'] *= max_weight

    relaxed_resources = {}
    resources = []

    for person_id in agents:
        if isinstance(person_id, str) and "***" in person_id: #ignore dummy agents in relaxations
            continue
        if person_id in participate:
            continue

        if 'min_age' in porder.keys():
            resource_attrp = resource_attr[person_id]
        else:
            resource_attrp = resource_attr
        #print(partitions)
        for partition in partitions:
            p_c += 1
            counter += 1
            pref_copy = copy.deepcopy(pref_attr[person_id])

            if len(pref_copy) == 0:
                break

            cost = 1
            for key in porder:
                budget = partition[porder[key]]
                thresh = values[person_id][(key, pref_copy[key])]

                while budget > 0 and thresh > 0:
                    budget -= 1
                    thresh -= cost
                pref_copy[key] = (opp_values[person_id][(key, thresh)][1])

            if not resources:
                resources = resource_attrp.keys()

            available_resources = set()
            for resource in resources:
                att = resource_attrp[resource]
                if satisfied_thresh(values, person_id, att, pref_copy):
                    consumed = cost_consumed(values, person_id, resource_attrp[resource],
                                             copy.deepcopy(pref_attr[person_id]))
                    available_resources.add((resource, consumed))

            mx = (1 + len(agents)) * max_weight

            for resource in available_resources:  # assigning weights to relaxed edges. The weights of the original
                # edges were defined in preprocess/preprocess_data.py
                if not g_alt.has_edge(person_id, resource[0]):
                    # agents
                    if weight == 0:
                        sub = 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        #print("adding resource with cost", resource[1])
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    if weight == 1:
                        sub = resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        # mx = greatest cost.
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    elif weight == 2:
                        sub = (lagents * lresources + 1) ** resource[1]  # note that in the specific structure of the
                        # costs cost can be used as the \pi function.
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # cost then leximin
                    elif weight == 3:
                        sub = resource[1] * (lagents * lresources + 1) * (lagents * lresources + 1) ** budge + (
                                lagents * lresources + 1) ** resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # agent then leximin
                    elif weight == 4:
                        sub = 1 * (lagents * lresources + 1) * (lagents * lresources + 1) ** budge + (
                                lagents * lresources + 1) ** resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # lexi then cost
                    elif weight == 5:
                        sub = (lagents * lresources + 1) ** resource[1] * (lagents * lresources + 1) * budge + resource[
                            1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # agent then cost
                    elif weight == 6:
                        sub = (lagents * lresources + 1) * budge + resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # lexi then agent
                    elif weight == 7:
                        sub = (lagents * lresources + 1) ** resource[1] * (lagents * lresources + 1) + 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # cost then agent
                    elif weight == 8:
                        sub = resource[1] * (lagents * lresources + 1) + 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])

                    if (person_id, resource[0]) not in relaxed_resources:
                        relaxed_resources[(person_id, resource[0])] = set()
                    relaxed_resources[(person_id, resource[0])].add(partition)

    return g_alt, relaxed_resources


def relax_all(g, resource_attr_1, pref_attr_1, budge, agents, values, opp_values, porder, weight):
    # this function adds all edges with cost<\infty to the graph.
    import copy

    resource_attr = copy.deepcopy(resource_attr_1)
    pref_attr = copy.deepcopy(pref_attr_1)
    values = copy.deepcopy(values)
    opp_values = copy.deepcopy(opp_values)
    gr = g.copy()

    if 'min_age' in porder.keys():
        for item in agents:
            person_id = item
            break
        resource_attrp = resource_attr[person_id]
    else:
        resource_attrp = resource_attr

    lagents = len(agents)
    lresources = len(resource_attrp.keys())

    max_weight = calc_max_weight(len(agents), len(resource_attrp.keys()), weight, budge)

    counter = 0
    import copy

    partitions = get_alpha_partitions(budge, len(porder.keys()))

    p_c = 0
    g_alt = copy.deepcopy(gr)
    for edge in g_alt.edges(data=True):
        edge[2]['weight'] *= max_weight

    relaxed_resources = {}
    resources = []

    for person_id in agents:
        if isinstance(person_id,str) and "***" in person_id: #ignore dummy agents in relaxations
            continue
        if 'min_age' in porder.keys():
            resource_attrp = resource_attr[person_id]
        else:
            resource_attrp = resource_attr
        #print(partitions)
        for partition in partitions:
            p_c += 1
            counter += 1
            pref_copy = copy.deepcopy(pref_attr[person_id])

            if len(pref_copy) == 0:
                break

            cost = 1
            for key in porder:
                budget = partition[porder[key]]
                thresh = values[person_id][(key, pref_copy[key])]

                while budget > 0 and thresh > 0:
                    budget -= 1
                    thresh -= cost
                pref_copy[key] = (opp_values[person_id][(key, thresh)][1])

            if not resources:
                resources = resource_attrp.keys()

            available_resources = set()
            for resource in resources:
                attrval = resource_attrp[resource]
                if satisfied_thresh(values, person_id, attrval, pref_copy):
                    consumed = cost_consumed(values, person_id, resource_attrp[resource],
                                             copy.deepcopy(pref_attr[person_id]))
                    available_resources.add((resource, consumed))

            mx = (1 + len(agents)) * max_weight

            for resource in available_resources:  # assigning weights to relaxed edges. The weights of the original
                # edges were defined in preprocess/preprocess_data.py
                if not g_alt.has_edge(person_id, resource[0]):
                    # agents
                    if weight == 0:
                        sub = 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        #print("adding resource with cost", resource[1])
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    if weight == 1:
                        sub = resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        # mx = greatest cost.
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    elif weight == 2:
                        sub = (lagents * lresources + 1) ** resource[1]  # note that in the specific structure of the
                        # costs cost can be used as the \pi function.
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # cost then leximin
                    elif weight == 3:
                        sub = resource[1] * (lagents * lresources + 1) * (lagents * lresources + 1) ** budge + (
                                lagents * lresources + 1) ** resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # agent then leximin
                    elif weight == 4:
                        sub = 1 * (lagents * lresources + 1) * (lagents * lresources + 1) ** budge + (
                                lagents * lresources + 1) ** resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # lexi then cost
                    elif weight == 5:
                        sub = (lagents * lresources + 1) ** resource[1] * (lagents * lresources + 1) * budge + resource[
                            1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # agent then cost
                    elif weight == 6:
                        sub = (lagents * lresources + 1) * budge + resource[1]
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # lexi then agent
                    elif weight == 7:
                        sub = (lagents * lresources + 1) ** resource[1] * (lagents * lresources + 1) + 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])
                    # cost then agent
                    elif weight == 8:
                        sub = resource[1] * (lagents * lresources + 1) + 1
                        w = mx - sub
                        if w < 0:
                            raise Exception("negative weight")
                        g_alt.add_edge(person_id, resource[0], weight=w, cost=resource[1])

                    if (person_id, resource[0]) not in relaxed_resources:
                        relaxed_resources[(person_id, resource[0])] = set()
                    relaxed_resources[(person_id, resource[0])].add(partition)
    return g_alt, relaxed_resources


def participate_in_all_matchings(g):  # not in use. Calculate the set of agents that participate in
    # all maximum matchings of graph g.
    top = {n for n, d in g.nodes(data=True) if d["bipartite"] == 0}
    mmsz = len(nx.bipartite.maximum_matching(g, top_nodes=top))
    part = []
    for agent in top:
        g_temp = g.copy()
        g_temp.remove_node(agent)
        topr = set(top)
        topr.remove(agent)
        mmsz2 = len(nx.bipartite.maximum_matching(g_temp, top_nodes=topr))
        if mmsz > mmsz2:
            part.append(agent)
    return part


def create_am_subsets(data_list):  #auxilary function for generate_msizes
    shuffled_list = data_list.copy()
    random.shuffle(shuffled_list)
    subsets = {}

    for size in range(len(data_list) + 1):
        subsets[size] = shuffled_list[:size]

    return subsets


def generate_msizes(grn, relaxations, matching):  # a function for determining the matching size when only some of the
    # agents are willing to relax their restrictions.
    agents = {n for n, d in grn.nodes(data=True) if d["bipartite"] == 0}
    resources = {n for n, d in grn.nodes(data=True) if d["bipartite"] == 1}

    already = set()
    edges = {}

    for x, y in matching:  # some technical code for collecting the edges dictionary
        # with an agent and a set of possible relaxed edges.
        if x in agents:
            agent = x
            resource = y
        else:
            agent = y
            resource = x
        if agent in already:
            continue

        if (agent, resource) in relaxations.keys():
            if agent not in edges:
                edges[agent] = set()
            edges[agent].add(resource)
        already.add(agent)

    if len(edges) == 0:
        return []
    # in this stage we have the original graph and a set of relaxing agents, each agent with its relaxable edges.
    subsets = create_am_subsets(list(edges.keys()))

    # for each subset generate graph and calculate size of maximum matching
    retval = []

    for ind, subset in subsets.items():
        graph = copy.deepcopy(grn)
        cnt = 0
        if len(subset) > 0:
            for agent in subset:
                for edge in edges[agent]:
                    graph.add_edge(agent, edge)
                cnt += 1

        msize = matching_size(agents, dict(nx.bipartite.maximum_matching(graph, top_nodes=agents)))
        esize = cnt
        retval.append((ind, msize, esize))

    return retval


def calc_relaxing_count_and_costs(gr, matching, relaxations, top_nodes):
    cntset = set()
    matching = dict(matching)
    costs = []
    for x, y in matching.items():
        if (x, y) in relaxations.keys() or (y, x) in relaxations.keys():
            costs.append(gr[x][y]['cost'])
            if x in top_nodes:
                cntset.add(x)
            else:
                cntset.add(y)

    cnt = len(cntset)
    mx = 0
    sm = 0
    if cnt > 0:
        mx = max(costs)
        sm = sum(costs)

    return cnt, mx, sm
