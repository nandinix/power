import geopandas as gpd
import folium
from folium import plugins
import mapclassify
from matplotlib import pyplot as plt
import json
import pandas as pd
from branca.element import Template, MacroElement
from branca.colormap import linear
from jinja2 import Template

# add pop up for news, add option to view by score, add option for 10 year summary

# Read the CSV files
csv_file = 'PSVI_yearly.csv'
df = pd.read_csv(csv_file)

summary_file = 'PSVI_summary.csv'
sdf = pd.read_csv(summary_file)

# Ensure FIPS codes are strings and pad with leading zeros to ensure 5 digits
df['county'] = df['county'].astype(str).str.zfill(5)
sdf['fips_code'] = sdf['fips_code'].astype(str).str.zfill(5)

# Map categories to numeric values
category_map = {'Minor': 1, 'Moderate': 2, 'Major': 3, 'Severe': 4, 'Extreme': 5}

# Apply the mapping to the relevant columns
for year in range(2014, 2024):
    df[f'{year}_rate_numeric'] = df[f'{year}_rate'].map(category_map)

sdf['summary_numeric'] = sdf['PSVI_cluster'].map(category_map)

# Display the first few rows to verify the changes
print(df.head())
print(sdf.head())

shapefile = 'UScounties/UScounties.shp'
gdf = gpd.read_file(shapefile)



# Taking out Alaska and Hawaii
states_to_exclude = ['Alaska', 'Hawaii']
filtered_gdf = gdf[~gdf['STATE_NAME'].isin(states_to_exclude)]

# Ensure the FIPS code columns in both DataFrames have the same name
df.rename(columns={'county': 'FIPS'}, inplace=True)  # Rename if necessary
sdf.rename(columns={'fips_code': 'FIPS'}, inplace=True)  # Rename if necessary

# Convert the FIPS code to the same type (string) in both DataFrames
df['FIPS'] = df['FIPS'].astype(str)
sdf['FIPS'] = sdf['FIPS'].astype(str)
gdf['FIPS'] = gdf['FIPS'].astype(str)


# Perform a left merge to keep all entries from the shapefile
merged_gdf = filtered_gdf.merge(df, on='FIPS', how='left')
merged_gdf = merged_gdf.merge(sdf, on='FIPS', how='left')


# Fill missing values in the 'rate' and 'score' columns with "N/A"
for year in range(2014, 2024):
    merged_gdf[f'{year}_rate'] = merged_gdf[f'{year}_rate'].fillna("No Data")
    merged_gdf[f'{year}_score'] = merged_gdf[f'{year}_score'].fillna(0)
    merged_gdf[f'{year}_rate_numeric'] = merged_gdf[f'{year}_rate_numeric'].fillna(0)

merged_gdf['PSVI_score'] = merged_gdf['PSVI_score'].fillna(0)
merged_gdf['PSVI_cluster'] = merged_gdf['PSVI_cluster'].fillna("No Data")
merged_gdf['summary_numeric'] = merged_gdf['summary_numeric'].fillna(0)
    
print(merged_gdf.head())

# Save the merged GeoDataFrame to a new shapefile
merged_gdf.to_file('path_to_new_shapefile.shp')

powermap = folium.Map(location=[37.8, -96], zoom_start=5, zoom_control=False)


# Define color scale
def get_color(value):
    colors = {
        1: '#FFFEAF', # minor
        2: '#FECB5B', # moderate
        3: '#FD8D3B', # major
        4: '#F0482D', # severe
        5: '#C20424', # extreme
        0: '#EAEADC' # no data
    }
    return colors.get(value, '#d9d9d9')

colormap = linear.YlOrRd_09.scale(0, 125)

def add_geojsoncluster(map_obj, geo_df, year, column, layer_name):
    style_function = lambda feature: {
        'fillColor': get_color(feature['properties'][column]),
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.9
    }

    highlight_function = lambda feature: {
        'fillColor': '#ffff00', # highlight color
        'color': 'black',
        'weight': 1,
        'fillOpacity': 1
    }

    folium.GeoJson(
        geo_df,
        name=layer_name,
        style_function=style_function,
        highlight_function=highlight_function,
        # on_each_feature=on_each_feature(feature, layer),
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME', f'{year}_score', f'{year}_rate'],
            aliases=['County:', 'Score:', 'Cluster:'],
            localize=True
        )
    ).add_to(map_obj)


def add_geojsonscore(map_obj, geo_df, year, column, layer_name):
    style_function = lambda feature: {
        'fillColor': colormap(feature['properties'][column]),
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.9
    }

    highlight_function = lambda feature: {
        'fillColor': '#ffff00', # highlight color
        'color': 'black',
        'weight': 1,
        'fillOpacity': 1
    }

    folium.GeoJson(
        geo_df,
        name=layer_name,
        style_function=style_function,
        highlight_function=highlight_function,
        # on_each_feature=on_each_feature(feature, layer),
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME', f'{year}_score', f'{year}_rate'],
            aliases=['County:', 'Score:', 'Cluster:'],
            localize=True
        )
    ).add_to(map_obj)

# Add layers for each year
for year in range(2014, 2024):
    add_geojsoncluster(powermap, merged_gdf, year, f'{year}_rate_numeric', f'{year}')
    # add_geojsonscore(powermap, merged_gdf, year, f'{year}_score', f'{year} Score')


# Add layer for 10 year summary
style_function = lambda feature: {
        'fillColor': get_color(feature['properties']['summary_numeric']),
        'color': 'black',
        'weight': 0.2,
        'fillOpacity': 0.9
    }

highlight_function = lambda feature: {
        'fillColor': '#ffff00', # highlight color
        'color': 'black',
        'weight': 1,
        'fillOpacity': 1
    }

folium.GeoJson(
        merged_gdf,
        name='10 year summary',
        style_function=style_function,
        highlight_function=highlight_function,
        # on_each_feature=on_each_feature(feature, layer),
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME', 'PSVI_score', 'PSVI_cluster'],
            aliases=['County:', 'Score:', 'Cluster:'],
            localize=True
        )
    ).add_to(powermap)



# Custom JavaScript for radio buttons in LayerControl
script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    var layerControlInputs = document.querySelectorAll('.leaflet-control-layers-selector');
    layerControlInputs.forEach(function(input) {
        if (input.type === 'checkbox') {
            input.type = 'radio';
            input.name = 'leaflet-base-layers';
        }
    });
    
});
</script>
"""


# Add custom script to the map
powermap.get_root().html.add_child(folium.Element(script))

# Create a legend as a macro element
legend_html = """
<div style="
    position: fixed; 
    bottom: 30px; 
    right: 30px; 
    width: 150px; 
    height: 150px; 
    background-color: white; 
    border:2px solid grey; 
    border-radius:5px;
    z-index:9999; 
    font-size:10px;
    padding: 10px;
    ">
    <b>Legend</b> <br>
    <i style="background: #EAEADC; width: 15px; height: 15px; display: inline-block;"></i> No Data <br>
    <i style="background: #FFFEAF; width: 15px; height: 15px; display: inline-block;"></i> Minor <br>
    <i style="background: #FECB5B; width: 15px; height: 15px; display: inline-block;"></i> Moderate <br>
    <i style="background: #FD8D3B; width: 15px; height: 15px; display: inline-block;"></i> Major <br>
    <i style="background: #F0482D; width: 15px; height: 15px; display: inline-block;"></i> Severe <br>
    <i style="background: #C20424; width: 15px; height: 15px; display: inline-block;"></i> Extreme <br>
</div>
"""

# Add the legend to the map using DivIcon
legend = folium.DivIcon(
    icon_size=(150, 150),
    icon_anchor=(0, 0),
    html=legend_html,
)

legend_element = folium.Element(legend_html)
powermap.get_root().html.add_child(legend_element)

# Create a custom HTML element for the popup content
popup_html = """
<div class="custom-popup" style="
    position: fixed; 
    top: 20px; 
    left: 20px; 
    background-color: white; 
    border: 1px solid #ccc; 
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); 
    border-radius: 8px;
    z-index: 9999; 
    padding: 20px;
    max-width: 400px;
    font-family: Arial, sans-serif;
    color: #333;">

    <div style="position: relative;">
        <button onclick="togglePopup()" style="
            position: absolute; 
            top: -10px; 
            right: -10px; 
            background: #f5f5f5; 
            border: none; 
            border-radius: 50%; 
            width: 25px; 
            height: 25px; 
            font-size: 16px; 
            line-height: 20px; 
            cursor: pointer;
            color: #333;">&times;</button>
        <h4 style="margin: 0 0 10px 0;">Information</h4>
        <p style="margin: 0;">This is a sample popup with some information.</p>
    </div>
</div>

<button id="showPopupButton" onclick="togglePopup()" style="
    display: none; 
    position: fixed; 
    top: 20px; 
    left: 20px; 
    background: #007bff; 
    color: white; 
    border: none; 
    border-radius: 8px; 
    padding: 10px 20px; 
    font-size: 16px; 
    cursor: pointer;
    z-index: 9998;">Show Information</button>

<script>
function togglePopup() {
    var popup = document.querySelector('.custom-popup');
    var button = document.getElementById('showPopupButton');
    if (popup.style.display === 'none') {
        popup.style.display = 'block';
        button.style.display = 'none';
    } else {
        popup.style.display = 'none';
        button.style.display = 'block';
    }
}
</script>
"""


# Add the HTML element as a custom control to the map
popup = folium.Element(popup_html)
powermap.get_root().html.add_child(popup)


# Add layer control to toggle between years
folium.LayerControl(collapsed=False).add_to(powermap)


# Save the map
powermap.save('index.html')


