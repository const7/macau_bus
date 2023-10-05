"""
Description: Streamlit app for bus arrival time visualization
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 14:55:52
LastEditTime: 2023-10-05 22:13:38
"""

import sqlite3
import pandas as pd

import streamlit as st
import seaborn as sns
import plotly.express as px
from matplotlib import pyplot as plt
from matplotlib import font_manager

import config

# font_manager.fontManager.addfont("./data/Helvetica.ttf")
# plt.rcParams["font.family"] = "Helvetica"
st.set_option("deprecation.showPyplotGlobalUse", False)


# load station name dict
station2name = pd.read_csv(config.STATION_NAME_PATH, index_col=0)[
    "station_name"
].to_dict()
# Database connection
conn = sqlite3.connect(config.DATABASE_PATH)


# construct station name
def construct_station_name(station_code, station_index):
    # add "/1" to station code if not exist
    station_tmp_code = station_code if "/" in station_code else station_code + "/1"
    station_tmp_name = station2name.get(station_tmp_code, "未知站点")
    if station_index == 0:
        station_tmp_name += " (起点)"
    return f"[{station_index}] {station_code}-{station_tmp_name}"


def load_data(route):
    query = f"""
    SELECT DISTINCT station_code, station_index
    FROM bus_data
    WHERE route = '{route}'
    ORDER BY station_index
    """
    data = pd.read_sql(query, conn)
    data["station_name"] = data[["station_code", "station_index"]].apply(
        lambda row: construct_station_name(row["station_code"], row["station_index"]),
        axis=1,
    )
    station_options = [
        (name, (code, idx))
        for name, code, idx in zip(
            data["station_name"], data["station_code"], data["station_index"]
        )
    ]
    return station_options


def load_arrival_data(route, station_info):
    station_code, station_index = station_info
    query = f"""
    SELECT arrival_time
    FROM bus_data
    WHERE route = '{route}' AND station_code = '{station_code}' AND station_index = {station_index}
    """
    data = pd.read_sql(query, conn)
    print(data.head())
    data["minute"] = pd.to_datetime(data["arrival_time"]).dt.strftime("%H:%M")

    # Create a DataFrame with every minute of the day
    all_minutes = pd.date_range(start="00:00", end="23:59", freq="T").strftime("%H:%M")
    all_minutes_df = pd.DataFrame(all_minutes, columns=["minute"])

    # Group your data by minute and count the arrivals
    grouped_data = data.groupby("minute").size().reset_index(name="count")

    # Merge the grouped data with the all_minutes_df DataFrame to ensure data for every minute
    merged_data = pd.merge(
        all_minutes_df, grouped_data, on="minute", how="left"
    ).fillna(0)

    return merged_data


def plot_data(selected_route, selected_station_info):
    data = load_arrival_data(selected_route, selected_station_info)
    fig = px.line(data, x="minute", y="count")
    fig.update_traces(line=dict(color="green", width=1))
    fig.update_layout(
        title="Arrival Time Distribution",
        xaxis_title="Time of Day",
        yaxis_title="Frequency",
        template="plotly_white",
        margin=dict(l=0, r=0, t=40, b=40),
        xaxis=dict(tickangle=-90, nticks=10, tickfont=dict(size=14)),
    )
    st.plotly_chart(fig)


def plot_travel_time(route):
    query = f"SELECT * FROM bus_data WHERE route = '{route}' ORDER BY bus_plate, arrival_time, station_index"
    data = pd.read_sql(query, conn)
    data["arrival_datetime"] = pd.to_datetime(data["arrival_time"])
    data["station_name"] = data[["station_code", "station_index"]].apply(
        lambda row: construct_station_name(row["station_code"], row["station_index"]),
        axis=1,
    )
    station_id2name = (
        data[["station_index", "station_name"]]
        .drop_duplicates()
        .set_index("station_index")["station_name"]
        .to_dict()
    )
    # Sort the data by bus_plate, arrival_datetime, and station_index
    data_sorted = data.sort_values(
        by=["bus_plate", "arrival_datetime", "station_index"]
    )

    # Calculate the station index and travel time for the next station
    data_sorted["next_station_index"] = data_sorted.groupby("bus_plate")[
        "station_index"
    ].shift(-1)
    # convert seconds to minutes
    data_sorted["travel_time"] = (
        data_sorted.groupby("bus_plate")["arrival_datetime"]
        .diff()
        .shift(-1)
        .dt.total_seconds()
        / 60
    )

    # Exclude the last station and any rows where the next station is not the expected next station
    max_station_index = data_sorted["station_index"].max()
    filtered_data = data_sorted[
        (data_sorted["station_index"] != max_station_index)
        & (data_sorted["next_station_index"] == data_sorted["station_index"] + 1)
        & (data_sorted["next_station_index"].notna())
    ]

    # Plotting
    plt.figure(figsize=(10, 8))
    # Plot the average travel time as bars
    sns.barplot(
        x="travel_time",
        y="station_index",
        data=filtered_data,
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
        data=filtered_data,
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
        labels=[station_id2name[i] for i in range(int(max_station_index))],
        fontproperties=font_manager.FontProperties(family="SimHei", size=15),
    )
    return plt.gcf()  # return the current figure


def main():
    st.title("Bus Arrival Time Distribution")

    # Load unique routes from the database
    routes = pd.read_sql("SELECT DISTINCT route FROM bus_data", conn)

    # User input in the sidebar
    with st.sidebar:
        st.header("Settings")
        selected_route = st.selectbox("Select a route", routes["route"])
        # Load stations based on selected route
        station_options = load_data(selected_route)
        _, selected_station_info = st.selectbox(
            "Select a station", options=station_options, format_func=lambda x: x[0]
        )

    # Plot data for Arrival Time Distribution on the main page
    st.subheader("Arrival Time Distribution")
    plot_data(selected_route, selected_station_info)

    # Plot data for Average Travel Time Between Stations on the main page
    st.subheader("当前站到下一站的平均时间")
    fig = plot_travel_time(selected_route)
    st.pyplot(fig)  # Render the travel time plot in Streamlit


if __name__ == "__main__":
    main()
