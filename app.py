"""
Description: Streamlit app for bus arrival time visualization
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 14:55:52
LastEditTime: 2023-11-03 17:04:48
"""

import sqlite3

# web app
import streamlit as st
import streamlit.components.v1 as components

# load config
import config
from src import data_processing
from src import data_visualization

config = config.Config()


def build_bus_selection(conn):
    # st.header("澳门巴士")
    # Load unique routes from the database
    routes = data_processing.get_route_data(conn)
    selected_route = st.selectbox("选择巴士路线", routes["route"])
    return selected_route


def build_wait_time(conn, route):
    # recent start time
    st.subheader("预计候车时间")
    # Load stations based on selected route
    station_data, _, _ = data_processing.get_station_data(conn, route)
    station_options = data_processing.get_station_options(station_data)
    _, station_info = st.selectbox(
        "选择候车站点", options=station_options[:-1], format_func=lambda x: x[0]
    )
    # if in the first station
    if station_info[1] == 0:
        recent_start_df = data_processing.get_recent_start(conn, route, station_info)
        st.caption("你位于起点站，这是最近3次起点站发车时间")
        st.table(recent_start_df)
        return
    # get travel data
    travel_time_df = data_processing.get_travel_time(conn, route)
    if travel_time_df.empty:
        st.caption("前方暂无车辆")
    # get recent bus
    else:
        data = data_processing.get_recent_bus(conn, route, station_info, travel_time_df)
        st.caption(f"前方有 {len(data)} 辆车")
        st.table(data)


def build_travel_time(conn, route):
    st.subheader("任意两站之间旅行时间")
    # get data
    travel_time_df = data_processing.get_travel_time(conn, route)
    # build selectbox
    station_data, _, _ = data_processing.get_station_data(conn, route)
    station_options = data_processing.get_station_options(station_data)
    station1_col, station2_col = st.columns([1, 1])
    with station1_col:
        start_name, code_and_index = st.selectbox(
            "选择起点", options=station_options[:-1], format_func=lambda x: x[0]
        )
    with station2_col:
        start_index = station_options.index((start_name, code_and_index))
        end_name, _ = st.selectbox(
            "选择终点",
            options=station_options[start_index + 1 :],
            format_func=lambda x: x[0],
        )
    t_df = travel_time_df.query(
        f"start_name == '{start_name}' and end_name == '{end_name}'"
    )
    st.pyplot(data_visualization.plot_station_wise_travel(t_df))


def build_bis_iframe(route):
    with st.expander("查看实时路线及位置"):
        iframe_height = 500
        route_line_col, route_map_col = st.columns([3, 2])
        with route_line_col:
            components.iframe(
                f"https://bis.dsat.gov.mo:37812/macauweb/map.html?routeName={route}&routeCode={route.zfill(5)}",
                height=iframe_height,
            )
        with route_map_col:
            components.iframe(
                f"https://bis.dsat.gov.mo:37812/macauweb/routeLine.html?routeName={route}",
                height=iframe_height,
            )


def main():
    # st.title("澳门巴士数据")
    # connet to database
    with sqlite3.connect(config.DATABASE_PATH) as conn:
        # sidebar (user input)
        selected_route = build_bus_selection(conn)
        # recent start time
        build_wait_time(conn, selected_route)
        # bis iframe
        build_bis_iframe(selected_route)
        # travel time
        build_travel_time(conn, selected_route)


if __name__ == "__main__":
    main()
