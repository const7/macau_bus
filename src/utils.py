"""
Description: Utils functions for the project
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-06 16:02:53
LastEditTime: 2023-12-11 02:38:57
"""

import hashlib
import requests
import pandas as pd
from datetime import datetime
from .config import config


def get_api_response(route):
    """Post request to get bus info.
    Parameters
    ----------
    route : str
        Route id like 701X, 71, 72, 73, 73S, N6
    Returns
    -------
    response : requests.Response
        Response from bus request
    """

    # build token in header
    def get_token(route):
        """Construct token for bus request."""

        # get md5 hash
        def get_bus_md5(payload):
            # suffix like "action=dy&routeName=73&dir=0&lang=zh-tw&device=web"
            bus_url_suffix = "&".join([f"{k}={v}" for k, v in payload.items()])
            return hashlib.md5(bus_url_suffix.encode("utf-8")).hexdigest()

        # add bus id to payload
        payload = config.FIX_PAYLOAD.copy()
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

    headers = config.HEADERS.copy()
    with requests.Session() as session:
        payload, headers["token"] = get_token(route)
        response = session.post(config.BUS_REQUEST_URL, headers=headers, data=payload)
        response.raise_for_status()
        return response


def load_scode2name(file_path=config.STATION_NAME_PATH):
    """Load station id to name mapping from csv.
    Parameters
    ----------
    file_path : str
        Path to the csv file
    """
    return pd.read_csv(file_path, index_col=0)["station_name"].to_dict()


def save_stationid2name_file(shp_path, outfile_path):
    """Read station names from GIS file and save as csv.
    Parameters
    ----------
    shp_path : str
        Path to the GIS file
    outfile_path : str
        Path to the output csv file
    """
    import geopandas as gpd  # GIS file read
    from zhconv import convert  # hant to hans

    # load data
    gdf = gpd.read_file(shp_path)
    # convert M11_1	to M11/1
    gdf["P_ALIAS"] = gdf["P_ALIAS"].str.replace("_", "/")
    # convert chinese traditional to simplified
    gdf["P_NAME"] = gdf["P_NAME"].apply(convert, args=("zh-hans",))
    gdf.rename(
        {"P_ALIAS": "station_code", "P_NAME": "station_name"}, inplace=True, axis=1
    )
    # save to csv
    gdf[["station_code", "station_name"]].to_csv(
        outfile_path, index=False, encoding="utf-8-sig"
    )
