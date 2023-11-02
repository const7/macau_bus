"""
Description: Streamlit app for bus arrival time visualization
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 14:55:52
LastEditTime: 2023-11-02 13:39:44
"""

import sqlite3

# web app
import streamlit as st
import streamlit.components.v1 as components

# laod config
import config
from src import data_processing
from src import data_visualization

config = config.Config()


def build_sidebar(conn):
    # Load unique routes from the database
    routes = data_processing.get_route_data(conn)

    # User input in the sidebar
    with st.sidebar:
        st.header("澳门巴士")
        selected_route = st.selectbox("选择巴士路线", routes["route"])
        # Load stations based on selected route
        station_data, _, _ = data_processing.get_station_data(conn, selected_route)
        station_options = [
            (f"[{idx}] {code}-{name}", (code, idx))
            for name, code, idx in zip(
                station_data["station_name"],
                station_data["station_code"],
                station_data["station_index"],
            )
        ]
        _, selected_station_info = st.selectbox(
            "选择站点", options=station_options, format_func=lambda x: x[0]
        )
    return selected_route, selected_station_info


def build_recent_start(conn, route, station_info):
    # recent start time
    st.subheader("最近三趟发车/到站时间")
    recent_start_df = data_processing.get_start_data(conn, route, station_info)
    st.table(recent_start_df)


def build_travel_time(conn, route):
    # average travel time
    st.subheader("当前站到下一站的平均时间")
    _, _, sid2name = data_processing.get_station_data(conn, route)
    travel_time_df = data_processing.get_travel_time(conn, route)
    fig = data_visualization.plot_travel_time(travel_time_df, sid2name)
    st.pyplot(fig)


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
        selected_route, selected_station_info = build_sidebar(conn)
        # recent start time
        build_recent_start(conn, selected_route, selected_station_info)
        # bis iframe
        build_bis_iframe(selected_route)

        # map_data = pd.DataFrame(
        #     np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4], columns=["lat", "lon"]
        # )
        # st.map(map_data)

        # # Plot data for Arrival Time Distribution on the main page
        # st.subheader("Arrival Time Distribution")
        # plot_data(selected_route, selected_station_info)

        # Plot data for Average Travel Time Between Stations on the main page
        build_travel_time(conn, selected_route)


if __name__ == "__main__":
    main()
