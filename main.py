import pystac_client
import rasterio
import geopandas as gpd
from pyproj import CRS
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Define the coordinate in EPSG:2056
x, y = 2574187.11, 1204941.00

#define datetime="2021-08-01/2024-08-31"
DATETIME = "2021-08-01/2024-08-31"

# Create a GeoDataFrame with the point
point = gpd.GeoDataFrame({'geometry': [Point(x, y)]}, crs='EPSG:2056')

# Transform the point to EPSG:4326 (WGS84) for STAC query
point_wgs84 = point.to_crs('EPSG:4326')
lon, lat = point_wgs84.geometry.x[0], point_wgs84.geometry.y[0]

# Connect to the STAC API
catalog = pystac_client.Client.open("https://data.geo.admin.ch/api/stac/v0.9/")

# Swisstopo finish : add the conformance classes :
catalog.add_conforms_to("COLLECTIONS")
catalog.add_conforms_to("ITEM_SEARCH")
#for collection in catalog.get_collections():
#    print(collection.id)


# Search for items
search = catalog.search(
    collections=["ch.swisstopo.swisseo_vhi_v100"],
    intersects={"type": "Point", "coordinates": [lon, lat]},
    datetime=DATETIME
)

items = list(search.items())
print(f"Found {len(items)} items")

results = []

for idx, item in enumerate(items, start=1):
    print(f"Processing item {idx} of {len(items)}")

    date = item.properties['datetime']

    # Get the URL for the BANDS-10M asset
    bands_10m_key = next(key for key in item.assets.keys() if key.endswith('_vegetation-10m.tif'))
    bands_10m_url = item.assets[bands_10m_key].href

    # Read the bands
    with rasterio.open(bands_10m_url) as src:
        # Get pixel coordinates
        py, px = src.index(x, y)

        # Read the pixel values
        #
        vhi_value = src.read(1, window=((py, py+1), (px, px+1)))[0, 0]


        # Append results without indexing into ndvi
        if 0 <= vhi_value <= 100:
            results.append({'date': date, 'VHI': vhi_value})

# Create a DataFrame from the results
df = pd.DataFrame(results)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
df.head()

breakpoint()
import matplotlib.pyplot as plt

# Filter the DataFrame to exclude zero NDVI values
filtered_df = df[df['NDVI'] > 0]

# Plotting the NDVI time series
plt.figure(figsize=(12, 6))
plt.plot(filtered_df['date'], filtered_df['VHI'], 'o-')
plt.title('VHI Time Series')
plt.xlabel('Date')
plt.ylabel('VHI')
plt.grid(True)
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.tight_layout()  # Adjust layout to prevent clipping of labels
plt.show()