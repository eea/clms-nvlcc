'''
This module contains functions for creating and displaying folium maps.
'''

import os
import folium
import warnings
import branca.colormap as cm
import numpy as np
from IPython.display import display, HTML

from modules.utils import define_colormap
from modules.regions_dict import regions_dict
from modules.images import read_image, save_as_png, match_array_shape
from modules.analysis import calculate_statistics_masked


def show_on_map(rasters_dir, chosen_region, base_map, layer_dicts):
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
                    
    Output: folium map of the chosen region with the selected layers
    '''
    
    # create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    map = folium.Map(location=coordinates, zoom_start=regions_dict[chosen_region][1])
    figure = folium.Figure(width=600, height=400)
    map = folium.Map(coordinates, zoom_start=regions_dict[chosen_region][1], tiles=base_map).add_to(figure)
    
    # add layers to the map
    for ds_properties in layer_dicts:
        
        dataset_label, layer_name, color_code, folium_color, reverse, opacity = (
            ds_properties['label'],
            ds_properties['layer_name'],
            ds_properties['color_code'],
            ds_properties['folium_color'],
            ds_properties['reverse'],
            ds_properties['opacity'],
        )
    
        # read the dataset into array
        dataset_dict = read_image(rasters_dir, chosen_region, dataset_label)
        arr, bounds, arr_min, arr_max = (
            dataset_dict['array'], 
            dataset_dict['bounds'], 
            dataset_dict['min_value'], 
            dataset_dict['max_value']
        )
        
        # save the array as a PNG file for folium
        os.makedirs('tmp', exist_ok=True)
        path_to_png = f'tmp/tmp_{dataset_label}.png'
        save_as_png(arr, path_to_png, color_code=color_code)

        # add the layer to the map
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
        
        # define and add colorbar to the map
        if folium_color:
            colormap = define_colormap(folium_color, arr_min, arr_max, reverse)
            map.add_child(colormap)

    # add layer control to the map
    folium.LayerControl().add_to(map)
    
    return map


def display_side_by_side(m1, m2): 
    '''
    Display two folium maps side by side.
    
    Input:
    - `m1, m2`: folium maps to be displayed
        
    Output: none
    '''
    
    with warnings.catch_warnings():
        # ignore UserWarnings (needed for HTML)
        warnings.simplefilter("ignore", UserWarning)

        # HTML code to display maps side by side
        htmlmap = HTML('<iframe srcdoc="{}" style="float:left; width: {}px; height: {}px; display:inline-block; width: 49%; margin: 0 auto; border: 2px solid black"></iframe>'
                '<iframe srcdoc="{}" style="float:right; width: {}px; height: {}px; display:inline-block; width: 49%; margin: 0 auto; border: 2px solid black"></iframe>'
                .format(m1.get_root().render().replace('"', '&quot;'),500,500,
                        m2.get_root().render().replace('"', '&quot;'),500,500))
        
    # display maps
    display(htmlmap)
    
    
def analyze_masked_area(rasters_dir, chosen_region, mask_below, clim, 
                            imd_layer_name, lst_layer_name, mask_by='LST'):
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
            
    Output: folium map of the chosen masked region with the selected layers
    '''

    # create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    map = folium.Map(location=coordinates, zoom_start=regions_dict[chosen_region][1])
    figure = folium.Figure(width=600, height=400)
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

    folium.LayerControl().add_to(map)
    
    imd_stats=calculate_statistics_masked(imd_arr, [0])
    lst_stats=calculate_statistics_masked(lst_arr, [])
    
    print(f"{imd_layer_name}\nMean: {imd_stats[0]:.2f}, Median: {imd_stats[1]:.2f}, 90th Percentile: {imd_stats[2]:.2f}\n")
    print(f"{lst_layer_name}\nMean: {lst_stats[0]:.2f}, Median: {lst_stats[1]:.2f}, 90th Percentile: {lst_stats[2]:.2f}")
    
    return map

     
    


    
    
    
    
