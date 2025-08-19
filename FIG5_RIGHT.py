import functools

from preprocess import preprocess_data
from util import relax_with_bound, relax_with_bound_mcfair
import os
from itertools import cycle

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


# code for generating the graphs in Figure 3.
def run(conf):
    dataset = 'mcld' if conf['dataset'] == "CHILD" else 'course_many'

    # loading the graphs and the restrictions data
    gr, gr2, gr3, n, m, resource_attr, pref_attr, values, opp_values, porder = preprocess_data.process(dataset)
    top_nodes = {n for n, d in gr.nodes(data=True) if d["bipartite"] == 0}

    guarantees = {'SNH-SB', 'SNH-WB', 'WNH-WB'}

    cost_threshold = 3  # which cost is considered as infinity?
    res = []
    exp_id = conf['exp_id']

    if conf['dataset'] in {'COURSE'}:
        ls = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]  # list of bounds for course and children datasets.
    elif conf['dataset'] == 'CHILD':
        ls = [0, 0.05, 0.1, 0.15, 0.2]  # list of bounds for course and children datasets.
    for threshold in ls:  # for each threshold
        for guarantee in guarantees:
            if guarantee == 'WNH-WB':  # gr has weights of WNH-WB
                msize = relax_with_bound(gr, resource_attr, pref_attr, cost_threshold, top_nodes, values, opp_values,
                                         porder,
                                         0, int(threshold * len(top_nodes)))  # do relaxations
                # and output allocation size
                res.append(
                    (exp_id, threshold, 'WNH-WB', msize / len(top_nodes)))

            elif guarantee == 'SNH-SB':  # gr has weights of SNH-SB
                msize = relax_with_bound(gr2, resource_attr, pref_attr, cost_threshold, top_nodes, values, opp_values,
                                         porder,
                                         0, int(threshold * len(top_nodes)))
                res.append(
                    (exp_id, threshold, 'SNH-SB', msize / len(top_nodes)))

            elif guarantee == 'SNH-WB':  # gr has function of SNH-WB
                msize = relax_with_bound_mcfair(gr3, resource_attr, pref_attr, cost_threshold, top_nodes, values,
                                                opp_values,
                                                porder,
                                                0, int(threshold * len(top_nodes)))
                res.append(
                    (exp_id, threshold, 'SNH-WB', msize / len(top_nodes)))

    return res


def run_experiment(dataset, exp_id):
    conf = dict()
    conf['exp_id'] = int(exp_id)
    conf['dataset'] = dataset
    conf['specific_threshold'] = 3  # threshold for running
    res = run(conf)
    return res


def store_results():  # store all dictionaries with the results for the run.
    res1 = []
    for res1_p in results:
        res1.extend(res1_p)

    df1 = pd.DataFrame(res1, columns=['exp_id', 'Cost Threshold', 'type', 'Ratio of Matched Agents'])
    df1.to_csv(os.path.join('.', 'output', 'df_FIG5_R_{}.csv'.format(dataset)), index=False)



def group_values(value):
        return value

def set_env():
    sns.set(font_scale=2)


def generate_graphs_f5R(datasets):  # plot the results
    set_env()
    for dataset in datasets:
        fp = './output/df_FIG5_R_{}.csv'.format(dataset)

        if os.path.exists(fp):
            plt.clf()
            ddf = pd.read_csv(fp.format(dataset))
            filtered_df = ddf[ddf['type'].isin(['WNH-WB', 'SNH-SB', 'SNH-WB'])]
            if 'CHILD' == dataset:
                filtered_df = filtered_df[filtered_df['Cost Threshold'].isin([0, 0.05, 0.1, 0.15, 0.2])]
                groups = 5
            else:
                filtered_df = filtered_df[filtered_df['Cost Threshold'].isin([0, 0.2, 0.4, 0.6, 0.8, 1.0])]
                groups = 6

            filtered_df['gtype'] = filtered_df['type'].apply(group_values)
            g1 = sns.barplot(data=filtered_df, x='Cost Threshold', y='Ratio of Matched Agents', hue='gtype',
                             hue_order=['SNH-SB', 'WNH-WB', 'SNH-WB'])
            hues = ['/', '|', 'x']

            it = cycle(hues)

            for i, bar in enumerate(plt.gca().patches):

                if i % groups == 0:
                    hue = next(it)
                if i == 0:
                    continue
                bar.set_hatch(hue)

            g1.set_title(dataset)

            if dataset == 'CHILD':
                plt.ylim(0.5, 0.8)
                g1.set_yticks([0.5, 0.6, 0.7, 0.8])
                g1.set_title('CHILD')
                g1.set_ylabel('Frac. of Matches')
            else:
                plt.ylim(0.2, 0.72)
                g1.set_yticks([0.2, 0.4, 0.6])

            g1.set_ylabel('Frac. of Matches')

            g1.set_xlabel('Max. Approached Agen.')
            g1.legend().set_title(None)
            if dataset == 'COURSE':
                plt.legend(loc = "lower center")
            else:
                g1.legend().set_visible(False)
            if dataset == 'CHILD':
                g1.lines[5].remove()
                g1.patches[5].remove()

                g1.lines[9].remove()
                g1.patches[9].remove()
            else:
                g1.lines[6].remove()
                g1.patches[6].remove()

                g1.lines[11].remove()
                g1.patches[11].remove()

            g1.patches[0].set_facecolor('black')

            fl = "./images/FIG5_R_" + dataset + ".pdf"

            # Get the current x-axis labels
            current_labels = plt.xticks()[1]
            # Define the new label for a specific category (e.g., 'Thur')
            new_label = 'Baseline'
            # Replace the label for the specific category
            new_labels = [new_label if label.get_text() == '0' else label.get_text() for label in current_labels]
            # Set the new x-axis labels
            plt.xticks(plt.xticks()[0], new_labels)

            if os.path.exists(fl):
                os.remove(fl)
            else:
                print("The file does not exist")

            plt.savefig(fl, format="pdf", bbox_inches="tight")
            plt.clf()


datasets = {'CHILD', 'COURSE'}

for dataset in datasets:
        results = map(functools.partial(run_experiment, dataset),
                      range(10))  # range stores the number of repetitions.
        store_results()


generate_graphs_f5R(datasets)
