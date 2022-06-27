import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import glob

data_folder = "data_logs/plot_data/"

experiment_filelabels = ["exp_1_lead_data_*","exp_2_lead_data_*"]
exp_group_names = ["IoRT Experiment 1:\nStationary+Leader","IoRT Experiment 2:\nFollower+Leader"]

for exp_group_idx, filelabel in enumerate(experiment_filelabels):
    exp_files = glob.glob(data_folder+filelabel)
    timestamp_arr = []
    ewma_arr = []
    for file_name in exp_files:
        df = pd.read_csv(file_name, sep=";")
        timestamp_data = df.loc[:, "timestamp"].to_numpy()
        ewma_data = df.loc[:, "ewma"].to_numpy()
        if len(timestamp_data) > 10 and len(ewma_data) > 10:
            timestamp_arr.append(timestamp_data)
            ewma_arr.append(ewma_data)

    # Plotting
    ax_list = []
    i = 0
    n_datasets = len(timestamp_arr)
    color_list = "bgrcmykw"
    fig = plt.figure()

    for i in range(n_datasets):
        ax = plt.subplot(1, n_datasets, i + 1)
        ax_list.append(ax)
        line_color = color_list[i % len(color_list)]
        line_name = "{}.{}".format(exp_group_idx+1, i+1)

        ax.plot(timestamp_arr[i], ewma_arr[i], color=line_color, label=line_name, linestyle="-")
        ax.set_aspect('auto')
        #ax.set_xbound(lower=0.0)
        ax.set_ybound(lower=-80, upper=-20)
        plt.title(line_name)
        plt.grid()

    #plt.xlim(0, 200)

    ax_list[0].get_shared_y_axes().join(ax_list[0], *ax_list)
    # for (i,axe) in enumerate(ax_list):
    #    axe.set_xlim([0, max(timestamp_arr[i] + 10)])
    # plt.autoscale(enable=True)
    fig.supxlabel("time\n(seconds)")
    fig.supylabel("RSSI\n(unitless)")
    fig.suptitle(exp_group_names[exp_group_idx])


    # Legend containing all the subfigure lines
    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    fig.legend(lines, labels, loc="upper left")
    plt.show()

if __name__ == '__main__':
    pass
