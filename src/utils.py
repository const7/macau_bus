import pandas as pd


def get_station_name(sid2name, station_code, station_index):
    """Construct station name.
    Parameters
    ----------
    sid2name : dict
        Station id to station name dict
    station_code : str
        Station code like T530
    station_index : int
        Station index in the route

    Returns
    -------
    station_name : str
        Station name
    """
    # add "/1" to station code if not exist
    station_tmp_code = station_code if "/" in station_code else station_code + "/1"
    station_name = sid2name.get(station_tmp_code, "未知站点")
    if station_index == 0:
        station_name += " (起点)"
    return station_name


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
