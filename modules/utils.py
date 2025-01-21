import os
import ipywidgets as widgets
from IPython.display import display
import branca.colormap as cm
import numpy as np


def list_filepaths(dir, patterns_in, patterns_out, include_all_patterns=True, print_warning=True):
    
    '''
    List of filepaths in a dir that contain all patterns in patterns_in, 
    and do not contain any of the patterns in patterns_out.
    include_all_patterns: if True, all patterns in patterns_in are required in a single filename.
    If False, any of the patterns in patterns_in is sufficeint. 
    (Note: include_all_patterns does not apply to pattern out - ALL patterns in patterns_out are always excluded)
    print_warning: if True, print a warning if no paths are found for the specified patterns.
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



# TBD!!!! change region-->area

def choose_region(regions_dict):

    # Define the dropdown menu for selecting a region
    region_dropdown = widgets.Dropdown(
        options=list(regions_dict.keys()),
        value=list(regions_dict.keys())[0],
        description='Region:'
    )

    # Define a variable to store the chosen value
    chosen_region = [region_dropdown.value]

    # Define a callback function to update the variable when the dropdown value changes
    def on_region_change(change):
        # global chosen_region
        chosen_region[0] = change['new']

    # Attach the callback function to the dropdown menu
    region_dropdown.observe(on_region_change, names='value')

    # Display the dropdown menu
    display(region_dropdown)
    
    return chosen_region


def choose_lower_bound(limits, description, step=2):
    
    l_min = round(limits[0] / step) * step
    l_max = round(limits[1] / step) * step
    
    options = np.arange(l_min, l_max + step, step).tolist()

    # Define the dropdown menu for selecting the minimum temperature
    dropdown = widgets.Dropdown(
        options=options,
        value=options[0],
        description=description
    )

    # Define a variable to store the chosen value
    mask_below = [dropdown.value]  # Use a mutable object (list)

    # Define a callback function to update the variable when the dropdown value changes
    def on_change(change):
        mask_below[0] = change['new']  # Update the value in the list

    # Attach the callback function to the dropdown menu
    dropdown.observe(on_change, names='value')

    # Display the dropdown menu
    display(dropdown)
    
    return mask_below




def define_colormap(folium_color, mmin, mmax, reverse=False):
    
    if reverse or folium_color == 'Spectral_04':
        clrs = cm.linear.__getattribute__(folium_color).colors.copy()
        clrs.reverse()
        colormap = cm.LinearColormap(colors=clrs).scale(mmin, mmax)
    else:
        colormap = cm.linear.__getattribute__(folium_color).scale(mmin, mmax)
        
    return colormap