"""
Description: Data visualization functions for web app
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-06 15:58:44
LastEditTime: 2023-10-07 13:30:01
"""

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
