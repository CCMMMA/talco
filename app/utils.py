from config import Config
from shapely.geometry import Point
import netCDF4


def get_index_lat_long(min_lat, max_lat, min_long, max_long):
    index_min_lat = round((min_lat - Config.wcm3_min_lat) / Config.delta_lat)
    index_max_lat = round((max_lat - Config.wcm3_min_lat) / Config.delta_lat)
    index_min_long = round((min_long - Config.wcm3_min_long) / Config.delta_long)
    index_max_long = round((max_long - Config.wcm3_min_long) / Config.delta_long)

    return index_min_lat, index_max_lat, index_min_long, index_max_long


def getConc(url, index_min_lat, index_min_long, index_max_lat, index_max_long):
    try:
        dataset = netCDF4.Dataset(url)
        lat_indices = range(index_min_lat - 2, index_max_lat + 2)
        lon_indices = range(index_min_long - 2, index_max_long + 2)
        concentration = dataset['conc'][0, 0, lat_indices, lon_indices]

        values = []
        for i in range(0, len(concentration)):
            for j in range(0, len(concentration[0])):
                current_value = concentration[i][j]
                values.append(current_value)

        value = sum(values)
    except Exception as e:
        print(e)
        value = 0

    return value
