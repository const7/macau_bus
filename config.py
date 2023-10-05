"""
Description: Config file for the project
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 21:52:12
LastEditTime: 2023-10-05 22:10:32
"""

# data collection log path
LOG_PAHT = "./data/bus_data_collection.log"
# station name path
STATION_NAME_PATH = "./data/station2name.csv"

# Routes to track
ROUTES = ["701X", "71", "72", "73", "73S", "N6"]
# bus post url
BUS_REQUEST_URL = "https://bis.dsat.gov.mo:37812/macauweb/routestation/bus"

# database path
DATABASE_PATH = "./data/bus_data.db"
# table creation
TABLE_CREATE_EXEC = "CREATE TABLE IF NOT EXISTS bus_data (route TEXT, bus_plate TEXT, station_code TEXT, arrival_time TEXT, station_index INT)"
