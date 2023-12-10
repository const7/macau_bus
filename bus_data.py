"""
Description: Collect bus data from Macau DSAT
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 14:07:46
LastEditTime: 2023-12-11 02:38:10
"""

import time
import logging
import requests
import sqlite3
from datetime import datetime

from src.config import config
from src import utils

# set logging config
logging.basicConfig(
    filename=config.LOG_PAHT,
    filemode="a",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Initialize bus station status & last seen timestamps for each bus
bus_station_status = {}
last_seen_timestamps = {}


def record_bus_arrival(conn, route, bus_plate, station_code, station_index):
    """Record bus arrival in database.

    Parameters
    ----------
    route : str
        Route id like 701X, 71, 72, 73, 73S, N6
    bus_plate : str
        Bus plate number
    station_code : str
        Station code like T530/1
    station_index : int
        Station index in the route
    """
    c = conn.cursor()
    arrival_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO bus_data VALUES (?,?,?,?,?)",
        (route, bus_plate, station_code, arrival_time, station_index),
    )
    conn.commit()
    # Log the arrival of the bus at the start station
    if station_index == 0:
        logging.info(
            f"{route}: Bus {bus_plate} arrived at station {station_code} ({station_index}) at {arrival_time}"
        )


def process_response(conn, route, response_json):
    """Process response from bus request.
    Parameters
    ----------
    conn : sqlite3.Connection
        Connection to the storage database
    route : str
        Route id like 701X, 71, 72, 73, 73S, N6
    response_json : dict
        Response from bus request
    """
    # Get route info
    route_info = response_json.get("data", {}).get("routeInfo", [])
    if not route_info:
        logging.error("routeInfo is empty")
        return
    # Get bus info in each station
    for station_index, station in enumerate(route_info):
        station_code = station["staCode"]
        # Combine route station_code and station_index to identify the station
        station_key = (route, station_code, station_index)
        for bus in station.get("busInfo", []):
            bus_plate = bus["busPlate"]
            status = bus["status"]
            # Get the previous status and pass count of the bus
            previous_status = bus_station_status.get(bus_plate, {}).get(
                station_key, None
            )
            # at the start station;
            # status changes from 1/None to 0, which means the bus just left the station
            if station_index == 0 and previous_status != status and status == "0":
                # clear the old bus status
                bus_station_status.pop(bus_plate, None)
                record_bus_arrival(conn, route, bus_plate, station_code, station_index)
            # For other stations, record the arrival time when status changes from 0/None to 1
            elif station_index > 0 and previous_status != status and status == "1":
                record_bus_arrival(conn, route, bus_plate, station_code, station_index)
            # Update the bus station status
            bus_station_status.setdefault(bus_plate, {})[station_key] = status
            # update last seen timestamp if status changes
            if previous_status != status:
                last_seen_timestamps[bus_plate] = datetime.now().timestamp()
    # Call cleanup function after processing the response
    cleanup_old_data()


def cleanup_old_data():
    # Get current timestamp
    current_timestamp = datetime.now().timestamp()
    # Remove data for buses not seen for STALE_THRESHOLD_MINUTES minutes
    stale_timestamp = current_timestamp - config.STALE_THRESHOLD_MINUTES * 60
    stale_buses = [
        bus_plate
        for bus_plate, timestamp in last_seen_timestamps.items()
        if timestamp < stale_timestamp
    ]
    for bus_plate in stale_buses:
        bus_station_status.pop(bus_plate, None)
        last_seen_timestamps.pop(bus_plate, None)


def main():
    """Main function to fetch bus data.
    Parameters
    ----------
    routes : list
        Route id list like ["701X", "71", "72", "73", "73S", "N6"]
    """
    with sqlite3.connect(config.DATABASE_PATH) as conn:
        # setup table connection
        c = conn.cursor()
        c.execute(config.TABLE_CREATE_EXEC)
        conn.commit()
        # Start fetching data
        while True:
            for route in config.ROUTES:
                try:
                    response = utils.get_api_response(route)
                    process_response(conn, route, response.json())
                except requests.RequestException as e:
                    logging.error(f"Failed to fetch API data for route {route}: {e}")
                except Exception as e:
                    logging.error(f"An error occurred for route {route}: {e}")
            time.sleep(config.SLEEP_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
