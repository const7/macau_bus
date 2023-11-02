"""
Description: Collect bus data from Macau DSAT
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 14:07:46
LastEditTime: 2023-11-02 13:39:30
"""

import time
import logging
import hashlib
import requests
import sqlite3
from datetime import datetime

import config

# load config
config = config.Config()
# set logging config
logging.basicConfig(
    filename=config.LOG_PAHT,
    filemode="a",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# remove data from the cache if it is older than this (minutes)
STALE_THRESHOLD_MINUTES = 30
# how long to sleep between posts (seconds)
SLEEP_INTERVAL_SECONDS = 5

# Initialize bus station status & last seen timestamps for each bus
bus_station_status = {}
last_seen_timestamps = {}

# Setup post request data
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47"
}

# post data
fix_payload = {
    "action": "dy",
    # direction: 0 or 1; always 0 for loop line
    "dir": "0",
    "lang": "zh-tw",
    "device": "web",
}


# build token in header
def get_token(route, payload=fix_payload):
    """Construct token for bus request.
    Parameters
    ----------
    route : str
        Route id like 701x, 71, 72, 73, 73S, N6
    payload : dict
        Fixed payload for bus request

    Returns
    -------
    token : str
        Token for bus request
    """

    # get md5 hash
    def get_bus_md5(payload):
        # suffix like "action=dy&routeName=73&dir=0&lang=zh-tw&device=web"
        bus_url_suffix = "&".join([f"{k}={v}" for k, v in payload.items()])
        return hashlib.md5(bus_url_suffix.encode("utf-8")).hexdigest()

    # add bus id to payload
    payload["routeName"] = route
    bus_md5 = get_bus_md5(payload)
    # get current time and format in "YYYYMMDDHHmm"
    current_time = datetime.now().strftime("%Y%m%d%H%M")
    # concatenate token and current time
    return (
        payload,
        bus_md5[:4]
        + current_time[:4]
        + bus_md5[4:12]
        + current_time[4:8]
        + bus_md5[12:24]
        + current_time[8:]
        + bus_md5[24:],
    )


def record_bus_arrival(conn, route, bus_plate, station_code, station_index):
    """Record bus arrival in database.

    Parameters
    ----------
    route : str
        Route id like 701x, 71, 72, 73, 73S, N6
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


def get_api_response(route):
    """Post request to get bus info.
    Parameters
    ----------
    route : str
        Route id like 701x, 71, 72, 73, 73S, N6
    Returns
    -------
    response : requests.Response
        Response from bus request
    """
    with requests.Session() as session:
        payload, headers["token"] = get_token(route)
        response = session.post(config.BUS_REQUEST_URL, headers=headers, data=payload)
        response.raise_for_status()
        return response


def process_response(conn, route, response_json):
    """Process response from bus request.
    Parameters
    ----------
    conn : sqlite3.Connection
        Connection to the storage database
    route : str
        Route id like 701x, 71, 72, 73, 73S, N6
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
    stale_timestamp = current_timestamp - STALE_THRESHOLD_MINUTES * 60
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
        Route id list like ["701x", "71", "72", "73", "73S", "N6"]
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
                    response = get_api_response(route)
                    process_response(conn, route, response.json())
                except requests.RequestException as e:
                    logging.error(f"Failed to fetch API data for route {route}: {e}")
                except Exception as e:
                    logging.error(f"An error occurred for route {route}: {e}")
            time.sleep(SLEEP_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
