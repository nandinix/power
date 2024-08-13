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


## DATA PROCESSING ##

yearbegin = 2014
yearend = 2024 # not inclusive

# # Read the CSV files
# csv_file = 'PSVI_yearly.csv'
# df = pd.read_csv(csv_file)

# summary_file = 'PSVI_summary.csv'
# sdf = pd.read_csv(summary_file)

# # Ensure FIPS codes are strings and pad with leading zeros to ensure 5 digits
# df['county'] = df['county'].astype(str).str.zfill(5)
# sdf['fips_code'] = sdf['fips_code'].astype(str).str.zfill(5)

# # Map categories to numeric values
# category_map = {'Minor': 1, 'Moderate': 2, 'Major': 3, 'Severe': 4, 'Extreme': 5}

# # Apply the mapping to the relevant columns
# for year in range(yearbegin, yearend):
#     df[f'{year}_rn'] = df[f'{year}_rate'].map(category_map)

# sdf['sum_rn'] = sdf['PSVI_cluster'].map(category_map)

# # Display the first few rows to verify the changes
# print(df.head())
# print(sdf.head())

# shapefile = 'UScounties/UScounties.shp'
# gdf = gpd.read_file(shapefile)

# # Taking out Alaska and Hawaii
# states_to_exclude = ['Alaska', 'Hawaii']
# filtered_gdf = gdf[~gdf['STATE_NAME'].isin(states_to_exclude)]

# # Ensure the FIPS code columns in both DataFrames have the same name
# df.rename(columns={'county': 'FIPS'}, inplace=True)  # Rename if necessary
# sdf.rename(columns={'fips_code': 'FIPS'}, inplace=True)  # Rename if necessary

# # Convert the FIPS code to the same type (string) in both DataFrames
# df['FIPS'] = df['FIPS'].astype(str)
# sdf['FIPS'] = sdf['FIPS'].astype(str)
# gdf['FIPS'] = gdf['FIPS'].astype(str)


# # Perform a left merge to keep all entries from the shapefile
# merged_gdf = filtered_gdf.merge(df, on='FIPS', how='left')
# merged_gdf = merged_gdf.merge(sdf, on='FIPS', how='left')


# # Fill missing values in the 'rate' and 'score' columns with "N/A"
# for year in range(yearbegin, yearend):
#     merged_gdf[f'{year}_rate'] = merged_gdf[f'{year}_rate'].fillna("No Data")
#     merged_gdf[f'{year}_score'] = merged_gdf[f'{year}_score'].fillna(0)
#     merged_gdf[f'{year}_rn'] = merged_gdf[f'{year}_rn'].fillna(0)

# merged_gdf['PSVI_score'] = merged_gdf['PSVI_score'].fillna(0)
# merged_gdf['PSVI_cluster'] = merged_gdf['PSVI_cluster'].fillna("No Data")
# merged_gdf['sum_rn'] = merged_gdf['sum_rn'].fillna(0)
    
# print(merged_gdf.head())

# # Save the merged GeoDataFrame to a new shapefile
# merged_gdf.to_file('powerdata/powerdata.shp')

powerfile = 'powerdata/powerdata.shp'
powergdf = gpd.read_file(powerfile)
# print(powergdf.columns)

## CREATING MAP ##

powermap = folium.Map(location=[37.8, -96], tiles="Cartodb Positron", zoom_start=5, zoom_control=False)


# Define color scale
def get_color(value):
    colors = {
        1: '#546CB8', # minor
        2: '#6399C3', # moderate
        3: '#ECD670', # major
        4: '#D2766D', # severe
        5: '#B84E5F', # extreme
        0: '#CCCCCC' # no data
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
for year in range(yearbegin, yearend):
    add_geojsoncluster(powermap, powergdf, year, f'{year}_rn', f'{year}')
    # add_geojsonscore(powermap, powergdf, year, f'{year}_score', f'{year} Score')


# Add layer for 10 year summary
style_function = lambda feature: {
        'fillColor': get_color(feature['properties']['sum_rn']),
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
        powergdf,
        name='10 year summary',
        style_function=style_function,
        highlight_function=highlight_function,
        # on_each_feature=on_each_feature(feature, layer),
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME', 'PSVI_score', 'PSVI_clust'],
            aliases=['County:', 'Score:', 'Cluster:'],
            localize=True
        )
    ).add_to(powermap)



# # Custom JavaScript for radio buttons in LayerControl
# script = """
# <script>
# document.addEventListener('DOMContentLoaded', function() {
#     var layerControlInputs = document.querySelectorAll('.leaflet-control-layers-selector');
#     layerControlInputs.forEach(function(input) {
#         if (input.type === 'checkbox') {
#             input.type = 'radio';
#             input.name = 'leaflet-base-layers';
#         }
#     });
    
# });
# </script>
# """

# # Add custom script to the map
# powermap.get_root().html.add_child(folium.Element(script))


script = """
<script>
function updateMap() {
    var selectedYear = document.getElementById('year-select').value;
    var layers = map._layers;
    
    // Loop through the layers and toggle visibility based on the selected year
    for (var layer in layers) {
        if (layers[layer].options && layers[layer].options.name) {
            var layerName = layers[layer].options.name;
            if (layerName.includes(selectedYear)) {
                layers[layer].addTo(map);
            } else {
                map.removeLayer(layers[layer]);
            }
        }
    }
}
</script>
"""

year_dropdown = """
<div id="year-dropdown" style="
    position: fixed; 
    top: 250px; 
    left: 20px; 
    z-index: 9999; 
    background: white; 
    border: 1px solid #ccc; 
    border-radius: 5px; 
    padding: 10px;">
    <label for="year-select">Select Year:</label>
    <select id="year-select" onchange="updateMap()">
        {% for year in range(""" + str(yearbegin) + ", " + str(yearend) + """) %}
        <option value="{{ year }}">{{ year }}</option>
        {% endfor %}
    </select>
</div>
"""

powermap.get_root().html.add_child(folium.Element(year_dropdown))
powermap.get_root().html.add_child(folium.Element(script))


# Create a legend as a macro element
legend_html = """
<div id="map-legend" class="legend">
    <h4>PSVI Cluster</h4>
    <div class="legend-item">
        <i style="background: #d73027;"></i><span>Extreme</span>
    </div>
    <div class="legend-item">
        <i style="background: #fc8d59;"></i><span>Severe</span>
    </div>
    <div class="legend-item">
        <i style="background: #fee08b;"></i><span>Major</span>
    </div>
    <div class="legend-item">
        <i style="background: #91bfdb;"></i><span>Moderate</span>
    </div>
    <div class="legend-item">
        <i style="background: #4575b4;"></i><span>Minor</span>
    </div>
    <div class="legend-item">
        <i style="background: #f0f0f0;"></i><span>No data</span>
    </div>
</div>

<style>
    #map-legend {
        position: absolute;
        bottom: 20px;
        left: 20px;
        z-index: 9999;
        background: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ccc;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
        line-height: 18px;
        color: #555;
        font-size: 14px;
        font-family: 'Arial', sans-serif;
        width: 150px;
    }

    #map-legend h4 {
        margin: 0 0 10px;
        font-weight: bold;
    }

    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }

    .legend-item i {
        width: 18px;
        height: 18px;
        display: inline-block;
        margin-right: 8px;
        border: 1px solid #999;
        border-radius: 3px;
    }

    .legend-item span {
        font-size: 13px;
        color: #333;
    }
</style>
"""

legend_element = folium.Element(legend_html)
powermap.get_root().html.add_child(legend_element)

# Create a custom HTML element for the popup content
popup_html = """
<div class="custom-popup" style="
    position: fixed; 
    top: 150px; 
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
    top: 200px; 
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


# Create a custom HTML element for the header
header_html = """
<div style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: #383838;
    border-bottom: 2px solid #cccccc;
    z-index: 9999;
    padding: 10px 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: Arial, sans-serif;
">
    <div style="display: flex; align-items: center;">
        <h1 style="margin: 30px; font-size: 30px; color: #e1e1e1;"><strong>Power System Vulnerability Index</strong></h1>
    </div>
    <div style="display: flex; align-items: center;">
        <a href="URL_TO_LAB_WEBSITE" style="
            background-color: transparent;
            color: #ffffff;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            font-size: 16px;
            margin-right: 30px;
            transition: background-color 0.3s ease, color 0.3s ease;
        "
        onmouseover="this.style.backgroundColor='#e1e1e1'; this.style.color='#000000';"
        onmouseout="this.style.backgroundColor='transparent'; this.style.color='#e1e1e1';"
        >About Us</a>
        <img src="URL_TO_LAB_LOGO" alt="Lab Logo" style="height: 80px; margin-right: 20px;">
        
    </div>
</div>
"""

# Replace URL_TO_UNIVERSITY_LOGO and URL_TO_LAB_LOGO with actual URLs of your logos
header_html = header_html.replace("URL_TO_UNIVERSITY_LOGO", "images/civillogo.png")
header_html = header_html.replace("URL_TO_LAB_LOGO", "images/URAIlogo.png") # Replace with actual lab logo URL
header_html = header_html.replace("URL_TO_LAB_WEBSITE", "https://www.urbanresilience.ai/")

# Add the header to the map
header = folium.Element(header_html)
powermap.get_root().html.add_child(header)

# # Add some CSS to create padding for the header
# padding_css = """
# <style>
#     #map {
#         padding-top: 200px; /* Adjust based on your header height */
#     }
# </style>
# """
# padding_element = folium.Element(padding_css)
# powermap.get_root().html.add_child(padding_element)


# Add layer control to toggle between years
# folium.LayerControl(collapsed=False).add_to(powermap)


# Save the map
powermap.save('index.html')


