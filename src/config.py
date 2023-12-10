"""
Description: Config file for the project
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 21:52:12
LastEditTime: 2023-12-11 02:56:42
"""

from pathlib import Path

# get paths
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Config class for the project"""

    # data dir
    DATA_DIR = BASE_DIR / "data"
    # DATA_DIR.mkdir(exist_ok=True)
    TRAVEL_TIME_DIR = DATA_DIR / "travel_time"
    TRAVEL_TIME_DIR.mkdir(exist_ok=True)

    # data collection log path
    LOG_PAHT = DATA_DIR / "bus_data_collection.log"
    # database path
    DATABASE_PATH = DATA_DIR / "bus_data.db"
    # station name path
    STATION_SHP_PATH = DATA_DIR / "bus_public_data" / "BUS_POLE.shp"
    STATION_NAME_PATH = DATA_DIR / "station2name.csv"

    # for data collection
    # Routes to track
    ROUTES = ["701X", "71", "72", "73", "73S", "N6"]
    # bus post url
    BUS_REQUEST_URL = "https://bis.dsat.gov.mo:37812/macauweb/routestation/bus"
    # remove data from the cache if it is older than this (minutes)
    STALE_THRESHOLD_MINUTES = 30
    # how long to sleep between posts (seconds)
    SLEEP_INTERVAL_SECONDS = 5
    # Setup post request data
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47"
    }
    # post data
    FIX_PAYLOAD = {
        "action": "dy",
        # direction: 0 or 1; always 0 for loop line
        "dir": "0",
        "lang": "zh-tw",
        "device": "web",
    }

    # for database table
    # table creation
    TABLE_CREATE_EXEC = "CREATE TABLE IF NOT EXISTS bus_data (route TEXT, bus_plate TEXT, station_code TEXT, arrival_time TEXT, station_index INT)"


# create config instance
config = Config()

if __name__ == "__main__":
    print(BASE_DIR)
