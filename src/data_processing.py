"""
Description: Data processing functions for web app
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 22:19:45
LastEditTime: 2023-10-07 14:16:06
"""

import pandas as pd
import streamlit as st
from . import utils


# raw station code to name mapping
scode2name = utils.load_scode2name(utils.STATION_NAME_PATH)


def get_station_name(station_code, station_index):
    """Construct station name.
    Parameters
    ----------
    station_code : str
        Station code like T530
    station_index : int
        Station index in the route

    Returns
    -------
    station_name : str
        Station name
    """
    # add "/1" to station code if not exist
    station_tmp_code = station_code if "/" in station_code else station_code + "/1"
    station_name = scode2name.get(station_tmp_code, "未知站点")
    if station_index == 0:
        station_name += " (起点)"
    return station_name


@st.cache_data
def get_route_data(_conn):
    """Get route data from database.
    Parameters
    ----------
    _conn : sqlite3.Connection
        Connection to the storage database
    """
    query = "SELECT DISTINCT route FROM bus_data"
    return pd.read_sql(query, _conn)


@st.cache_data
def get_station_data(_conn, route):
    """Get station data based on selected routes.
    Parameters
    ----------
    _conn : sqlite3.Connection
        Connection to the storage database
    route : str
        Route id like 701X, 71, 72, 73, 73S, N6
    """
    query = f"""
    SELECT DISTINCT station_code, station_index
    FROM bus_data
    WHERE route = '{route}'
    ORDER BY station_index
    """
    data = pd.read_sql(query, _conn)
    data["station_name"] = data.apply(
        lambda row: get_station_name(row["station_code"], row["station_index"]),
        axis=1,
    )
    scode2name = dict(zip(data["station_code"], data["station_name"]))
    sid2name = dict(zip(data["station_index"], data["station_name"]))
    return data, scode2name, sid2name


def get_start_data(conn, route, station_info):
    """Get most recent 3 start time of the route.

    Parameters
    ----------
    conn : sqlite3.Connection
        Connection to the storage database
    route : str
        Route id like 701X, 71, 72, 73, 73S, N6
    station_info : tuple
        Station code and station index

    Returns
    -------
    data: pd.DataFrame
        Most recent 3 start time of the route
    """
    _, station_index = station_info
    query = f"SELECT * FROM bus_data WHERE route = '{route}' AND station_index = {station_index} ORDER BY arrival_time DESC LIMIT 3"
    data = pd.read_sql(query, conn)
    data["station_name"] = data.apply(
        lambda x: f"{x['station_code']}-{get_station_name(x['station_code'], x['station_index'])}",
        axis=1,
    )
    data.rename(
        {
            "route": "路线",
            "bus_plate": "车牌",
            "station_name": "站点",
            "arrival_time": "发车/到站时间",
        },
        inplace=True,
        axis=1,
    )
    return data[["路线", "车牌", "站点", "发车/到站时间"]]


@st.cache_data
def get_arrival_data(_conn, route, station_info):
    station_code, station_index = station_info
    query = f"""
    SELECT arrival_time
    FROM bus_data
    WHERE route = '{route}' AND station_code = '{station_code}' AND station_index = {station_index}
    """
    data = pd.read_sql(query, _conn)
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


@st.cache_data
def get_travel_time(_conn, route):
    query = f"SELECT * FROM bus_data WHERE route = '{route}' ORDER BY bus_plate, arrival_time, station_index"
    data = pd.read_sql(query, _conn)
    data["arrival_datetime"] = pd.to_datetime(data["arrival_time"])
    data["station_name"] = data[["station_code", "station_index"]].apply(
        lambda x: f"[{x['station_index']}] {x['station_code']}-{get_station_name(x['station_code'], x['station_index'])}",
        axis=1,
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
    # remove outliers
    grouped_data = filtered_data.groupby(["station_index", "next_station_index"])
    travel_time_stats = grouped_data["travel_time"].agg(["mean", "std"]).reset_index()
    merged_data = pd.merge(
        filtered_data, travel_time_stats, on=["station_index", "next_station_index"]
    )
    merged_data["z_score"] = (
        merged_data["travel_time"] - merged_data["mean"]
    ) / merged_data["std"]
    final_data = merged_data[merged_data["z_score"].abs() <= 3]

    return final_data
