"""
Description: Data visualization functions for web app
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-06 15:58:44
LastEditTime: 2023-11-02 22:39:49
"""

import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager


# def plot_timeseries(conn, route, selected_station_info):
#     data = load_arrival_data(conn, route, selected_station_info)
#     fig = px.line(data, x="minute", y="count")
#     fig.update_traces(line=dict(color="green", width=1))
#     fig.update_layout(
#         title="Arrival Time Distribution",
#         xaxis_title="Time of Day",
#         yaxis_title="Frequency",
#         template="plotly_white",
#         margin=dict(l=0, r=0, t=40, b=40),
#         xaxis=dict(tickangle=-90, nticks=10, tickfont=dict(size=14)),
#     )
#     st.plotly_chart(fig)


@st.cache_data
def plot_station_wise_travel(data):
    mean_travel_time = data["travel_time"].mean()
    std_travel_time = data["travel_time"].std()
    lb_travel_time = mean_travel_time - 3 * std_travel_time
    ub_travel_time = mean_travel_time + 3 * std_travel_time
    # Plotting
    ax = sns.histplot(x="travel_time", data=data, color="gray", alpha=0.5)
    ax.set_xlabel("Travel time (s)")
    ax.set_ylabel("")
    ax.axvline(mean_travel_time, color="green", linestyle="--")
    ax.axvline(lb_travel_time, color="gray", linestyle="--")
    ax.axvline(ub_travel_time, color="gray", linestyle="--")
    # add mean annotation
    ax.text(
        mean_travel_time * 1.1,
        ax.get_ylim()[1] * 0.9,
        f"Mean:\n{mean_travel_time / 60:.1f} min",
        ha="center",
        va="center",
        color="green",
    )
    ax.text(
        lb_travel_time * 1.13,
        ax.get_ylim()[1] * 0.8,
        f"- 3 std:\n{lb_travel_time / 60:.1f} min",
        ha="center",
        va="center",
        color="red",
    )
    ax.text(
        ub_travel_time * 1.05,
        ax.get_ylim()[1] * 0.8,
        f"+ 3 std:\n{ub_travel_time / 60:.1f} min",
        ha="center",
        va="center",
        color="red",
    )
    return ax.get_figure()


@st.cache_data
def plot_travel_time(data, sid2name):
    """Plot the travel time bar between stations.

    Parameters
    ----------
    data : pd.DataFrame
        Travel time data
    sid2name : dict
        Station index to station name mapping

    Returns
    -------
    fig: matplotlib.figure.Figure
        Travel time bar plot
    """
    max_station_index = len(sid2name) - 1
    # Plotting
    plt.figure(figsize=(10, 8))
    # Plot the average travel time as bars
    sns.barplot(
        x="travel_time",
        y="station_index",
        data=data,
        color="lightgray",
        errorbar="sd",
        errwidth=2,
        capsize=0.1,
        orient="h",
    )
    # Overlay the standard deviation as red dots
    sns.stripplot(
        x="travel_time",
        y="station_index",
        data=data,
        jitter=True,
        size=4,
        color="green",
        alpha=0.6,
        orient="h",
    )
    # plt.title("Average Travel Time Between Stations")
    plt.xlabel(
        "分钟", fontproperties=font_manager.FontProperties(family="SimHei", size=15)
    )
    plt.ylabel("")
    plt.yticks(
        ticks=range(int(max_station_index)),
        labels=[sid2name[i] for i in range(int(max_station_index))],
        fontproperties=font_manager.FontProperties(family="SimHei", size=15),
    )
    return plt.gcf()
