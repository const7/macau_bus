"""
Description: Read station data from public GIS file and save to csv.
Author: Chen Kun
Email: chenkun_@outlook.com
Date: 2023-10-05 22:19:45
LastEditTime: 2023-10-05 22:21:54
"""

# GIS file read
import geopandas as gpd

# hant to hans
from zhconv import convert

# data source: https://data.gov.mo/Detail?id=e7b2e84d-3333-42f0-b676-64ce95306f0d
shp_path = "./bus_public_data/BUS_POLE.shp"


def read_station_names(shp_path):
    """Read station names from GIS file and save as csv.
    Parameters
    ----------
    shp_path : str
        Path to the GIS file
    """
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
        "./station2name.csv", index=False, encoding="utf-8-sig"
    )


if __name__ == "__main__":
    read_station_names(shp_path)
