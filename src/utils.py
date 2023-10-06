import pandas as pd
from pathlib import Path

# station id to name csv from preprocessed public data
STATION_NAME_PATH = Path(__file__).resolve().parent.parent / "data" / "station2name.csv"


# @st.cache_resource
def load_scode2name(file_path):
    print("testset")
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
