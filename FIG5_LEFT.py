import functools


import networkx as nx

from preprocess import preprocess_data
from util import relax_all_mcfair, relax_all, generate_msizes
import os

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


# code for generating the graphs in Figure 3.
def run(conf):
    res = []
    # loading the graphs and the restrictions data
    dataset = 'mcld' if conf['dataset'] == "CHILD" else 'course_many'

    gr, gr2, gr3, n, m, resource_attr, pref_attr, values, opp_values, porder = preprocess_data.process(dataset)
    top_nodes = {n for n, d in gr.nodes(data=True) if d["bipartite"] == 0}

    guarantees = {'SNH-SB', 'SNH-WB', 'WNH-WB'}

    cost_threshold = 3

    for guarantee in guarantees:
        if guarantee == 'WNH-WB':  # gr has weights of WNH-WB
            grn, relaxations = relax_all(gr, resource_attr, pref_attr, cost_threshold, top_nodes, values,
                                         opp_values, porder, 0)
        elif guarantee == 'SNH-SB':  # gr2 has weights of SNH-SB
            grn, relaxations = relax_all(gr2, resource_attr, pref_attr, cost_threshold, top_nodes, values,
                                         opp_values, porder, 0)
        elif guarantee == 'SNH-WB':  # gr3 has weights of SNH-WB
            grn, relaxations = relax_all_mcfair(gr3, resource_attr, pref_attr, cost_threshold, top_nodes, values,
                                                opp_values, porder, 0)

        matching = nx.max_weight_matching(grn)  # compute the weighted matching

        exp_id = conf['exp_id']

        msizes = generate_msizes(gr, relaxations, matching)
        for msize in msizes:
            res.append((exp_id, cost_threshold, guarantee, msize[0], msize[1] / len(top_nodes), msize[2]))

    return res


def run_experiment(dataset, exp_id):
    conf = dict()
    conf['exp_id'] = int(exp_id)
    conf['dataset'] = dataset
    conf['specific_threshold'] = 3  # threshold for running
    res = run(conf)
    return res


def store_results():  # store all dictionaries with the results for the run.
    res = []
    for res1_p in results:
        res.extend(res1_p)
    df = pd.DataFrame(res, columns=['exp_id', 'Cost Threshold', 'type', 'Ind', 'Ratio of Matched Agents', 'Relaxed Agents'])
    df.to_csv(os.path.join('.', 'output', 'df_FIG5_L_{}.csv'.format(dataset)), index=False)


def group_values(value):
        return value

def set_env():
    sns.set(font_scale=2)


def generate_graphs_f5L(datasets): #plot the results
    set_env()
    plt.clf()

    for dataset in datasets:
        fp = './output/df_FIG5_L_{}.csv'.format(dataset)

        if os.path.exists(fp):
            plt.clf()
            ddf = pd.read_csv(fp.format(dataset))

        filtered_df = ddf[ddf['type'].isin(['WNH-WB', 'SNH-SB', 'SNH-WB'])]

        filtered_df['gtype'] = filtered_df['type'].apply(group_values)

        g6 = sns.lineplot(data=filtered_df, x='Relaxed Agents', y='Ratio of Matched Agents', errorbar=('ci', 95), hue='gtype',
                            hue_order=['SNH-SB','WNH-WB', 'SNH-WB' ], style='gtype', style_order=['SNH-SB','SNH-WB','WNH-WB'],
                          dashes={'WNH-WB': (1, 1), 'SNH-WB': (3, 1, 1, 1), 'SNH-SB': (5, 2)}) #palette=['yellow', 'brown', 'purple']#)
        g6.legend_.set_title(None)
        g6.set_yticks([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
        g6.set_title(dataset)
        if dataset == 'COURSE':
            g6.set_ylabel('Frac. of Matches')
        else:
            g6.legend().set_visible(False)
            g6.set_ylabel('')

        g6.set_xlabel('Relaxing Agents')

        fl = "./images/FIG5_L_" + dataset + ".pdf"

        if os.path.exists(fl):
            os.remove(fl)
        else:
            print("The file does not exist")
        if dataset == "CHILD":
            plt.ylim(0.6, 0.8)
            g6.set_yticks([0.6, 0.65, 0.7, 0.75])
        if dataset == "COURSE":
            plt.ylim(0.2, 0.72)
            g6.set_yticks([0.2, 0.4, 0.6])

        plt.savefig(fl, format="pdf", bbox_inches='tight')
        plt.clf()



datasets = {'CHILD', 'COURSE'}

for dataset in datasets:
    results = map(functools.partial(run_experiment, dataset),
                      range(1))  # range stores the number of repetitions.
    store_results()

generate_graphs_f5L(datasets)
