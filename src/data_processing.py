"""
Description: Data processing functions for web app
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 22:19:45
LastEditTime: 2023-12-04 16:56:23
"""

import requests
import numpy as np
import pandas as pd
import streamlit as st
from . import utils


# raw station code to name mapping
scode2name = utils.load_scode2name(utils.STATION_NAME_PATH)


def get_station_name(station_code, station_index, full=False):
    """Construct station name.
    Parameters
    ----------
    station_code : str
        Station code like T530
    station_index : int
        Station index in the route
    full : bool, optional
        Whether to return full station name, by default False
        short name example: T550/3-澳门大学
        full name example: [0] T550/3-澳门大学（起点）

    Returns
    -------
    station_name : str
        Station name
    """
    # add "/1" to station code if not exist
    station_tmp_code = station_code if "/" in station_code else station_code + "/1"
    station_name = scode2name.get(station_tmp_code, "未知站点")
    if station_index == 0:
        station_name += "（起点）"
    station_name = f"{station_code}-{station_name}"
    if full:
        station_name = f"[{station_index}] {station_name}"
    return station_name


@st.cache_data
def get_route_data(_conn):
    """Get route data from database.
    Parameters
    ----------
    _conn : sqlite3.Connection
        Connection to the storage database
    """
    query = "SELECT DISTINCT route FROM bus_data ORDER BY route"
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
        lambda x: get_station_name(x["station_code"], x["station_index"], full=True),
        axis=1,
    )
    scode2name = dict(zip(data["station_code"], data["station_name"]))
    sid2name = dict(zip(data["station_index"], data["station_name"]))
    return data, scode2name, sid2name


@st.cache_data
def get_station_options(data):
    """Build station options for selectbox.
    Parameters
    ----------
    data : pd.DataFrame
        Station data
    Returns
    -------
    options : list
        Station options for selectbox in format of [(name, (code, idx))]
    """
    return [
        (name, (code, idx))
        for name, code, idx in zip(
            data["station_name"],
            data["station_code"],
            data["station_index"],
        )
    ]


@st.cache_data
def get_timetable_html(route):
    """Build bus timetable from tcm website.
    Parameters
    ----------
    route : str
        Bus route id like 701X, 71, 72, 73, 73S, N6
    Returns
    -------
    str or None
        html text
    """
    # get html
    response = requests.get(
        f"http://www.tcm.com.mo/web/station2/timeTable/{route}.html",
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"
        },
    )
    if response.status_code != 200:
        return None
    # html encoding
    if response.encoding != "utf-8":
        response.encoding = "utf-8"

    # build html
    css_style = """
    <style>
    table {
        width: 100% !important; /* Set table width to 100% */
        max-width: none !important; /* Remove max-width limitation */
        border-collapse: collapse; /* Collapse borders for a cleaner look */
        font-size: 12px; /* Decrease font size for a more compact display */
        line-height: 0.9; /* Reduce line height for a more compact layout */
    }
    table, th, td {
        border: 1px solid black; /* Add border styling (adjust as needed) */
        padding: 0px; /* Reduce cell padding for a more compact layout */
        text-align: center; /* Center-align text for better readability */
        vertical-align: middle; /* Vertically align text in cells */
    }
    </style>
    """
    html_content = """
    {css}
    <div id="table-container"></div>
    <script>
    function renderTable(content) {{
        var parser = new DOMParser();
        var doc = parser.parseFromString(content, 'text/html');
        var table = doc.querySelectorAll('table')[1]; // select the second table
        document.getElementById('table-container').innerHTML = table.outerHTML;
    }}
    renderTable(`{html}`);
    </script>
    """.format(
        css=css_style, html=response.text
    )
    return html_content


def get_recent_start(conn, route, station_info):
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
        lambda x: get_station_name(x["station_code"], x["station_index"]),
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


def get_recent_bus(conn, route, station_info, travel_df):
    """Get bus that started recently and have not arrived at the wait station.
    Parameters
    ----------
    conn : sqlite3.Connection
        Connection to the storage database
    route : str
        Route id
    station_info : tuple
        Station code and station index of the wait station
    travel_df : pd.DataFrame
        Travel time data
    """
    station_code, station_index = station_info
    max_wait_seconds = travel_df["travel_time"].max()
    query = f"""
    WITH MaxStationIndex AS (
        SELECT MAX(station_index) AS max_index
        FROM bus_data
        WHERE route = '{route}'
        AND arrival_time >= DATE('now', '-3 days')
    ),

    LatestDepartures AS (
        SELECT bus_plate, MAX(arrival_time) AS latest_departure_time
        FROM bus_data
        WHERE route = '{route}'
        AND station_index = 0
        GROUP BY bus_plate
    ),

    LatestRecords AS (
        SELECT t.bus_plate, MAX(t.arrival_time) AS latest_arrival_time
        FROM bus_data t
        JOIN LatestDepartures ld ON t.bus_plate = ld.bus_plate
        WHERE route = '{route}'
        AND t.arrival_time >= ld.latest_departure_time
        GROUP BY t.bus_plate
    )

    SELECT t.*
    FROM bus_data t
    JOIN LatestRecords lr ON t.bus_plate = lr.bus_plate AND t.arrival_time = lr.latest_arrival_time
    JOIN MaxStationIndex msi ON t.station_index < msi.max_index
    WHERE route = '{route}'
    AND t.station_index < {station_index}
    AND (julianday('now') - julianday(t.arrival_time)) * 86400 <= {max_wait_seconds}
    ORDER BY t.arrival_time DESC
    LIMIT 5;
    """
    data = pd.read_sql(query, conn)
    data["arrival_time"] = pd.to_datetime(data["arrival_time"])
    if data.empty:
        return pd.DataFrame(columns=["车牌", "当前站点", "预计等待时间", "最早到站时间", "最晚到站时间"])

    # get wait time information
    wait_station_name = get_station_name(station_code, station_index, full=True)

    def get_wait_time(row):
        curr_station_name = get_station_name(
            row["station_code"], row["station_index"], full=True
        )
        tmp_travel_df = travel_df.query(
            f"start_name == '{curr_station_name}' and end_name == '{wait_station_name}'"
        )
        if tmp_travel_df.empty:
            return np.nan, np.nan, np.nan
        mean_wait_seconds = tmp_travel_df["travel_time"].mean()
        std_wait_seconds = tmp_travel_df["travel_time"].std()
        average_arrival_time = row["arrival_time"] + pd.Timedelta(
            seconds=mean_wait_seconds
        )
        # use 2 sigma here based on the observation of the data distribution
        earliest_arrival_time = row["arrival_time"] + pd.Timedelta(
            seconds=mean_wait_seconds - 2 * std_wait_seconds
        )
        latest_arrival_time = row["arrival_time"] + pd.Timedelta(
            seconds=mean_wait_seconds + 2 * std_wait_seconds
        )
        return (
            mean_wait_seconds / 60,
            average_arrival_time,
            earliest_arrival_time,
            latest_arrival_time,
        )

    data[
        [
            "wait_time",
            "average_arrival_time",
            "earliest_arrival_time",
            "latest_arrival_time",
        ]
    ] = data.apply(get_wait_time, axis=1, result_type="expand")
    # format wait datetime
    data["wait_time"] = data["wait_time"].round(1).astype(str)
    # "%m-%d %H:%M:%S"
    data["average_arrival_time"] = pd.to_datetime(
        data["average_arrival_time"]
    ).dt.strftime("%H:%M:%S")
    data["earliest_arrival_time"] = pd.to_datetime(
        data["earliest_arrival_time"]
    ).dt.strftime("%H:%M:%S")
    data["latest_arrival_time"] = pd.to_datetime(
        data["latest_arrival_time"]
    ).dt.strftime("%H:%M:%S")

    # format data
    data["station_name"] = data.apply(
        lambda x: get_station_name(x["station_code"], x["station_index"]), axis=1
    )
    data.rename(
        {
            "bus_plate": "车牌",
            "station_name": "当前站点",
            "wait_time": "平均等待（分钟）",
            "average_arrival_time": "平均到站",
            "earliest_arrival_time": "预计最早",
            "latest_arrival_time": "预计最晚",
        },
        inplace=True,
        axis=1,
    )
    return data[["车牌", "当前站点", "平均等待（分钟）", "平均到站", "预计最早", "预计最晚"]]


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
    data["station_name"] = data.apply(
        lambda x: get_station_name(x["station_code"], x["station_index"], full=True),
        axis=1,
    )
    # detect new trip
    data["new_trip"] = (
        data["station_index"] <= data.groupby("bus_plate")["station_index"].shift(1)
    ) | (data["bus_plate"] != data["bus_plate"].shift(1))

    data["trip_id"] = data["new_trip"].cumsum()

    # calculate travel time
    def calculate_travel_times(group):
        times = group["arrival_datetime"].values
        stations = group["station_name"].values
        # get upper triangle index
        i, j = np.triu_indices(len(times), k=1)
        # get time differences (in seconds)
        travel_times = (times[j] - times[i]).astype("timedelta64[s]").astype(int)
        return pd.DataFrame(
            {
                "start_name": stations[i],
                "end_name": stations[j],
                "travel_time": travel_times,
            }
        )

    travel_times_df = (
        data.groupby("trip_id").apply(calculate_travel_times).reset_index(drop=True)
    )

    # remove outliers for each station pair
    def remove_outliers(group):
        # remove travel time longer than 2 hours
        group = group[group["travel_time"] <= 7200]
        # remove 3 sigma outliers
        mean_time = group["travel_time"].mean()
        std_time = group["travel_time"].std()
        group = group[
            (group["travel_time"] >= mean_time - 3 * std_time)
            & (group["travel_time"] <= mean_time + 3 * std_time)
        ]
        return group

    travel_times_df = (
        travel_times_df.groupby(["start_name", "end_name"])
        .apply(remove_outliers)
        .reset_index(drop=True)
    )
    return travel_times_df
