"""
Description: Config file for the project
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 21:52:12
LastEditTime: 2023-10-06 10:32:00
"""

from pathlib import Path

# get paths
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Config class for the project"""
    # data dir
    DATA_DIR = BASE_DIR / "data"
    # DATA_DIR.mkdir(exist_ok=True)

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

    # for database table
    # table creation
    TABLE_CREATE_EXEC = "CREATE TABLE IF NOT EXISTS bus_data (route TEXT, bus_plate TEXT, station_code TEXT, arrival_time TEXT, station_index INT)"

if __name__ == "__main__":
    print(BASE_DIR)
