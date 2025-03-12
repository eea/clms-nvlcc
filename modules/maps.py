'''
This module contains functions for creating and displaying folium maps.
'''

import os
import folium
import re
import numpy as np
import folium.plugins as plugins

from modules.regions_dict import regions_dict
from modules.utils import define_colormap
from modules.images import read_image, save_as_png, match_array_shape
from modules.analysis import calculate_statistics_masked


def prepare_layer_to_map(rasters_dir, chosen_region, layer_dict):
    '''
    Helper function to process a raster dataset, convert it to a PNG file, 
    and return properties for displaying on a Folium map.
    
    Input:
    - `rasters_dir (str)`: directory containing raster datasets.
    - `chosen_region (str)`: selected region name.
    - `layer_dict (dict)`: dictionary containing properties of the dataset.
        It should contain the following keys:
        - `label (str)`: label of the dataset
        - `layer_name (str)`: name to be displayed on the map
        - `color_code (str)`: color code to be used for the dataset
        - `folium_color (str)`: color code to be used for colorbar. If None, no colorbar is displayed.
        - `reverse (bool)`: whether to reverse the color code
        - `opacity (float)`: opacity of the layer

    Output:
    - `path_to_png (str)`: path to the saved PNG file.
    - `bounds (tuple)`: bounding box of the dataset.
    - `min_value (float)`: minimum value of the dataset.
    - `max_value (float)`: maximum value of the dataset.
    '''
    dataset_label = layer_dict['label']

    # read the dataset into an array
    dataset_dict = read_image(rasters_dir, chosen_region, dataset_label)
    arr, bounds, min_value, max_value = (
        dataset_dict['array'], 
        dataset_dict['bounds'], 
        dataset_dict['min_value'], 
        dataset_dict['max_value']
    )
    
    # save the array as a tmp PNG file for folium
    os.makedirs('tmp', exist_ok=True)
    path_to_png = f'tmp/tmp_{dataset_label}.png'
    save_as_png(arr, path_to_png, color_code=layer_dict['color_code'])

    return path_to_png, bounds, min_value, max_value


def display_map(rasters_dir, chosen_region, base_map, layer_dicts, map_size = (650, 400)):
    '''
    Create a folium map of the chosen region showing multiple layers.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters to be displayed
    - `chosen_region (str)`: name of the region to be displayed. Used to identify: 
        (1) the right images in rasters_dir, (2) the coordinates of the region and, 
        (3) zoom level for the map. 
    - `base_map (str)`: name of the base map to be used (e.g. 'OpenStreetMap')
    - `layer_dicts (list)`: list of dictionaries with properties of the layers to be displayed.
        Each dictionary should contain the following keys:
        - `label (str)`: label of the dataset
        - `layer_name (str)`: name to be displayed on the map
        - `color_code (str)`: color code to be used for the dataset
        - `folium_color (str)`: color code to be used for colorbar. If None, no colorbar is displayed.
        - `reverse (bool)`: whether to reverse the color code
        - `opacity (float)`: opacity of the layer
    - `map_size (tuple)`: size of the map in pixels (width, height). Default is (650, 400).
                    
    Output: folium map of the chosen region with the selected layers
    '''
    
    # create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    figure = folium.Figure(width=map_size[0], height=map_size[1])
    map = folium.Map(coordinates, zoom_start=regions_dict[chosen_region][1], tiles=base_map).add_to(figure)    

    # process and add layers to the map
    for layer_dict in layer_dicts:
        path_to_png, bounds, min_value, max_value = prepare_layer_to_map(rasters_dir, chosen_region, layer_dict)

        # add ImageOverlay to the map
        folium.raster_layers.ImageOverlay(
            image=path_to_png,
            name=layer_dict['layer_name'],
            bounds=bounds,
            opacity=layer_dict['opacity'],
            interactive=False,
            cross_origin=False,
            zindex=1,
            alt=layer_dict['layer_name']
        ).add_to(map)
        
        # define and add colorbar to the map
        if layer_dict['folium_color']:
            colormap = define_colormap(layer_dict['folium_color'], min_value, max_value, layer_dict['reverse'])
            map.add_child(colormap)

    # add layer control to the map
    folium.LayerControl(collapsed=False).add_to(map)
    
    # HTML custom title placement
    map_title = f'Selected region: {chosen_region}'
    title_html = f"""<h1 style="position:absolute;z-index:1000;top:12px;left:55px;font-size:16px;">{map_title}</h1>"""
    map.get_root().html.add_child(folium.Element(title_html))
    
    return map


def display_dual_map(rasters_dir, chosen_region, base_map, layer_1_dict, layer_2_dict):
    '''
    Create a folium DualMap to visualize two layers side by side.

    Input:
    - `rasters_dir (str)`: directory containing raster datasets.
    - `chosen_region (str)`: selected region name.
    - `base_map (str)`: base map name (e.g., 'OpenStreetMap').
    - `layer_1_dict (dict)`, `layer_2_dict (dict)`: dictionaries defining layer properties.
        Each dictionary should contain the following keys:
        - `label (str)`: label of the dataset
        - `layer_name (str)`: name to be displayed on the map
        - `color_code (str)`: color code to be used for the dataset
        - `folium_color (str)`: color code to be used for colorbar. If None, no colorbar is displayed.
        - `reverse (bool)`: whether to reverse the color code
        - `opacity (float)`: opacity of the layer

    Output:
    - `folium.plugins.DualMap` visualization.
    '''
    # get region coordinates and zoom level
    coordinates, zoom = regions_dict[chosen_region][:2]
    zoom += 1 # correction for DualMap
    

    # initialize the DualMap
    dual_map = plugins.DualMap(location=coordinates, tiles=None, zoom_start=zoom)

    # add base map to both sides
    for m in [dual_map.m1, dual_map.m2]:
        folium.TileLayer(base_map).add_to(m)

    # process both layers
    for layer_dict, map_side, side in zip([layer_1_dict, layer_2_dict], [dual_map.m1, dual_map.m2], ['left', 'right']):
        path_to_png, bounds, arr_min, arr_max = prepare_layer_to_map(rasters_dir, chosen_region, layer_dict)

        # add ImageOverlay to the corresponding side of the map
        folium.raster_layers.ImageOverlay(
            image=path_to_png,
            name=layer_dict['layer_name'],
            bounds=bounds,
            opacity=layer_dict['opacity'],
            interactive=False,
            cross_origin=False,
            zindex=1,
            alt=layer_dict['layer_name']
        ).add_to(map_side)
        
        # define and add colorbar to the map
        if layer_dict['folium_color']:
            colormap = define_colormap(layer_dict['folium_color'], arr_min, arr_max, layer_dict['reverse']) 
            
            # HTML custom colorbar placement
            colormap_html = colormap._repr_html_()
            colormap_html = re.sub(r'(\d+\.\d+)', lambda x: f"{int(float(x.group()))}", colormap_html)  # remove decimal points
            colormap_div = f"""<div style="position: absolute;z-index:1000;bottom:20px;{side}:250px;font-size:16px">{colormap_html}</div>"""
            dual_map.m1.get_root().html.add_child(folium.Element(colormap_div))

    # add layer control
    folium.LayerControl(collapsed=False).add_to(dual_map)
    
    # HTML custom title placement
    map_title = f'Selected region: {chosen_region}'
    title_html = f"""<h1 style="position:absolute;z-index:1000;top:20px;left:75px;font-size:18px;">{map_title}</h1>"""
    dual_map.m1.get_root().html.add_child(folium.Element(title_html))

    return dual_map

  
def display_analyze_masked_area(rasters_dir, chosen_region, mask_below, clim, 
                            imd_layer_name, lst_layer_name, mask_by='LST', map_size = (650, 400)):
    '''
    Generate a folium map of the chosen region with two layers (IMD and LST), 
    masked by the specified threshold.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters
    - `chosen_region (str)`: name of the region to be displayed. 
            Used to identify the right region images in `rasters_dir`.
    - `mask_below (float)`: mask values below this threshold
    - `clim (tuple)`: min and max values for the color scale
    - `imd_layer_name (str)`: name of the IMD layer to be displayed
    - `lst_layer_name (str)`: name of the LST layer to be displayed
    - `mask_by (str)`: which layer to use to mask by `mask_below`. 
            Default is `'LST'`.
    - `map_size (tuple)`: size of the map in pixels (width, height). Default is (650, 400).
            
    Output: folium map of the chosen masked region with the selected layers
    '''

    # create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    figure = folium.Figure(width=map_size[0], height=map_size[1])
    map = folium.Map(coordinates, zoom_start=regions_dict[chosen_region][1], tiles='Cartodb Positron').add_to(figure)

    # read IMD and LST into arrays
    im_dict = read_image(rasters_dir, chosen_region, 'IMD')
    imd_arr, imd_arr_min, imd_arr_max = im_dict['array'], im_dict['min_value'], im_dict['max_value']

    im_dict = read_image(rasters_dir, chosen_region, 'LST')
    lst_arr, lst_arr_min, lst_arr_max, bounds = im_dict['array'], im_dict['min_value'], im_dict['max_value'], im_dict['bounds']

    # match IMD and LST to the same shape
    imd_arr, lst_arr = match_array_shape(imd_arr, lst_arr, scaling_factor=7)

    # mask the values below the threshold
    if mask_by == 'LST':
        mask = np.where(lst_arr < mask_below)
    elif mask_by == 'IMD':
        mask = (imd_arr < mask_below) | np.isnan(imd_arr) | (imd_arr == 255)
    else:
        raise ValueError('Invalid mask_by argument. Choose from "LST" or "IMD".')
        
    lst_arr[mask] = np.nan
    imd_arr[mask] = np.nan

    # save arrays as a PNG file for folium
    os.makedirs('tmp', exist_ok=True)
    path_to_lst_png = f'tmp/tmp_masked_LST.png'
    save_as_png(lst_arr, path_to_lst_png, color_code='Spectral_r', clim=clim)

    path_to_imd_png = f'tmp/tmp_masked_IMD.png'
    save_as_png(imd_arr, path_to_imd_png, color_code='Reds', clim=(0,100))

    # add layers to the map
    imd_map_setup = {
        'path': path_to_imd_png, 
        'layer_name': imd_layer_name, 
        'color_code': 'Greys', 
        'opacity': 1, 
        'folium_color': None, 
        'reverse': False, 
        'min_value': imd_arr_min, 
        'max_value': imd_arr_max
    }
    lst_map_setup = {
        'path': path_to_lst_png, 
        'layer_name': lst_layer_name, 
        'color_code': 'Spectral_r', 
        'opacity': 1, 
        'folium_color': 'Spectral_04', 
        'reverse': True, 
        'min_value': clim[0], 
        'max_value': clim[1]
    }

    for setup in [imd_map_setup, lst_map_setup]:
        
        path_to_png, layer_name, color_code, opacity, folium_color, reverse, min_value, max_value = (
            setup['path'],
            setup['layer_name'],
            setup['color_code'],
            setup['opacity'],
            setup['folium_color'],
            setup['reverse'],
            setup['min_value'],
            setup['max_value']
        )

        folium.raster_layers.ImageOverlay(
            image=path_to_png,
            name=layer_name,
            bounds=bounds,
            opacity=opacity,
            interactive=False,
            cross_origin=False,
            zindex=1,
            alt=layer_name
        ).add_to(map)

        if folium_color:
            colormap = define_colormap(folium_color, min_value, max_value, reverse)
            map.add_child(colormap)

    # add layer control
    folium.LayerControl(collapsed=False).add_to(map)
    
    # HTML custom title placement
    map_title = f'Selected region: {chosen_region}'
    title_html = f"""<h1 style="position:absolute;z-index:1000;top:12px;left:55px;font-size:16px;">{map_title}</h1>"""
    map.get_root().html.add_child(folium.Element(title_html))
    
    
    # calculate statistics for the masked area
    imd_stats=calculate_statistics_masked(imd_arr, [0])
    lst_stats=calculate_statistics_masked(lst_arr, [])
    
    print(f"{imd_layer_name}\nMean: {imd_stats[0]:.2f}, Median: {imd_stats[1]:.2f}, 90th Percentile: {imd_stats[2]:.2f}\n")
    print(f"{lst_layer_name}\nMean: {lst_stats[0]:.2f}, Median: {lst_stats[1]:.2f}, 90th Percentile: {lst_stats[2]:.2f}")
    
    return map

     
    


    
    
    
    
