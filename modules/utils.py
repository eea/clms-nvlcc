import os
import ipywidgets as widgets
import branca.colormap as cm
import numpy as np
from IPython.display import display


def list_filepaths(dir, patterns_in, patterns_out, include_all_patterns=True, print_warning=True):
    '''
    List of filepaths in a dir that contain patterns in patterns_in, and do not contain patterns in patterns_out.
    
    Input:
    - `dir (str)`: path to the directory to be searched.
    - `patterns_in (list)`: list of patterns that the filenames should contain.
    - `patterns_out (list)`: list of patterns that the filenames should not contain.
    - `include_all_patterns (bool)`: if True, all patterns in patterns_in are required in a single filename.
            If False, any of the patterns in patterns_in is sufficeint. Default is True.
    - `print_warning (bool)`: if True, print a warning if no paths are found for the specified patterns. Default is True.
    
    Output:
    - list of filepaths that satisfy the specified conditions.
    '''
    
    if include_all_patterns:
        def patterns_in_bool(i):
            return all(pattern in i for pattern in patterns_in)
    else:
        def patterns_in_bool(i):
            return any(pattern in i for pattern in patterns_in)
        
    def patterns_out_bool(i):
        return all(pattern not in i for pattern in patterns_out)

    out = [os.path.join(dir,i) for i in os.listdir(dir) if patterns_in_bool(i) and patterns_out_bool(i)]
    
    if not out and print_warning:
        print(f'Warning! No paths found for the specified patterns ({patterns_in}) in {dir} (returning an empty list). ')
        
    return out


def choose_region(regions_dict):
    '''
    Generate a dropdown menu for selecting a region.
    
    Input:
    - `regions_dict (dict)`: dictionary with region names as keys and corresponding descriptions as values.
    
    Output:
    - chosen region (list with one element)
    '''

    # define a dropdown menu for selecting a region
    region_dropdown = widgets.Dropdown(
        options=list(regions_dict.keys()),
        value=list(regions_dict.keys())[0],
        description='Region:'
    )

    # define a variable to store the chosen value
    chosen_region = [region_dropdown.value]

    # define a callback function to update the variable when the dropdown value changes
    def on_region_change(change):
        # global chosen_region
        chosen_region[0] = change['new']

    # attach the callback function to the dropdown menu
    region_dropdown.observe(on_region_change, names='value')

    # display the dropdown menu
    display(region_dropdown)
    
    return chosen_region


def choose_lower_bound(limits, description, step=2):
    '''
    Generate a dropdown menu for selecting the lower bound of a range.
    
    Input:
    - `limits (list)`: list with the lower and upper bounds of the range.
    - `description (str)`: description of the dropdown menu.
    - `step (int)`: step size for the dropdown menu. Default is 2.
    
    Output:
    - chosen lower bound (list with one element)
    '''
    
    l_min = round(limits[0] / step) * step
    l_max = round(limits[1] / step) * step
    
    options = np.arange(l_min, l_max + step, step).tolist()

    # define the dropdown menu for selecting the lower bound
    dropdown = widgets.Dropdown(
        options=options,
        value=options[0],
        description=description
    )

    # define a variable to store the chosen value
    mask_below = [dropdown.value]  # use a mutable object (list)

    # define a callback function to update the variable when the dropdown value changes
    def on_change(change):
        mask_below[0] = change['new']  # update the value in the list

    # attach the callback function to the dropdown menu
    dropdown.observe(on_change, names='value')

    # display the dropdown menu
    display(dropdown)
    
    return mask_below


def define_colormap(folium_color, mmin, mmax, reverse=False):
    '''
    Define a colormap for folium maps.
    
    Input:
    - `folium_color (str)`: name of the colormap.
    - `mmin (float)`: minimum value for the colormap.
    - `mmax (float)`: maximum value for the colormap.
    - `reverse (bool)`: whether to reverse the colormap. Default is False.
    
    Output:
    - colormap object
    '''
        
    if reverse or folium_color == 'Spectral_04':
        clrs = cm.linear.__getattribute__(folium_color).colors.copy()
        clrs.reverse()
        colormap = cm.LinearColormap(colors=clrs).scale(mmin, mmax)
    else:
        colormap = cm.linear.__getattribute__(folium_color).scale(mmin, mmax)
        
    return colormap