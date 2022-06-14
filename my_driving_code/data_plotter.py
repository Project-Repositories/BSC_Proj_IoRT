import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

data_folder = "data_logs/"

experiment_1_name = "exp_1_lead_data_"



file_range = range(0, 3)
file_range = [str(num) for num in file_range]

timestamp_arr = []
ewma_arr = []
for file_num in file_range:
    file_name = data_folder + "exp_1_lead_data_{num}.csv".format(num=file_num)
    df = pd.read_csv(file_name, sep=";")
    timestamp_data = df.loc[:, "timestamp"].to_numpy()
    ewma_data = df.loc[:, "ewma"].to_numpy()
    if len(timestamp_data) > 10 and len(ewma_data) > 10:
        timestamp_arr.append(timestamp_data)
        ewma_arr.append(ewma_data)

if __name__ == '__main__':

    if True:
        ax_list = []
        i = 0
        n_datasets = len(timestamp_arr)
        color_list = "bgrcmykw"
        #fig, axes = plt.subplots(n_datasets, 1, sharey="all")
        fig = plt.figure()

        for i in range(n_datasets):
            # ax = axes[i]
            ax = plt.subplot(1, n_datasets, i + 1)
            ax_list.append(ax)
            line_color = color_list[i % len(color_list)]
            ax.plot(timestamp_arr[i], ewma_arr[i], color=line_color, label="2.{}".format(file_range[i]), linestyle="-")
            plt.title("2.{}".format(file_range[i]))
            plt.grid()
            plt.xlim(0, max(timestamp_arr[i]))
        ax_list[0].get_shared_y_axes().join(ax_list[0], *ax_list)
        plt.autoscale(enable=True)
        fig.supxlabel("time (seconds)")
        fig.supylabel("RSSI")
        fig.suptitle("Exp2")
        # plt.title("Exp2")
        lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        fig.legend(lines, labels)


    if False:
        n_datasets = len(timestamp_arr)
        color_list = "bgrcmykw"
        style_list = ["-", ":", "--", "-."]
        width_list = [1, 1.5, 1.8, 2.2]
        for i in range(n_datasets):
            line_color = color_list[i % len(color_list)]
            line_style = style_list[(i + 2) % len(style_list)]
            line_width = width_list[i % len(width_list)]
            plt.plot(timestamp_arr[i], ewma_arr[i], color=line_color, label="2.{}".format(file_range[i]),
                     linestyle=line_style,
                     linewidth=line_width, alpha=0.5)

    # plt.legend()
    plt.show()
    # print(df)
    # print(df.columns)
    # print(df.loc[:,"ewma"])
    # print(col0)
