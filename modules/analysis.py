import matplotlib
import matplotlib.pyplot as plt
import numpy as np  
from scipy.ndimage import zoom
import folium
import os

from modules.regions_dict import regions_dict
from modules.images import read_image, save_as_png
from modules.utils import define_colormap

def calculate_statistics(chosen_region, label, exclude_values=[]):
    
    output = read_image(chosen_region, label)
    arr, arr_min, arr_max = output['array'], output['min_value'], output['max_value']
    masked_arr = arr[~np.isin(arr, exclude_values)].flatten()
    
    mean_val = np.nanmean(masked_arr)
    median_val = np.nanmedian(masked_arr)
    percentile_90_val = np.nanpercentile(masked_arr, 90)
    
    min_val = np.nanmin(masked_arr)
    max_val = np.nanmax(masked_arr)
    
    output = {
        'mean': mean_val,
        'median': median_val,
        'percentile_90': percentile_90_val,
        'min': min_val,
        'max': max_val
    }

    return output


def plot_histograms(chosen_region, histogram_setups, figure_size=(12, 4), log_scale=False):

    fig, axes = plt.subplots(1, len(histogram_setups), figsize=figure_size)
    axes = np.atleast_1d(axes)  # Ensure axes is always an array

    for i, hist_setup in enumerate(histogram_setups):
                                
        color = hist_setup['color_code']
        label = hist_setup['label']
        exclude_values = hist_setup['exclude_values']
        name = hist_setup['layer_name']

        output = read_image(chosen_region, label)
        arr, arr_min, arr_max = output['array'], output['min_value'], output['max_value']

        # Normalize the data for color mapping
        norm = plt.Normalize(vmin=arr_min, vmax=arr_max)
        cmap = matplotlib.colormaps.get_cmap(color)

        # Get the histogram data
        hist_data, bins, _ = axes[i].hist(arr[~np.isin(arr, exclude_values)].flatten(), bins=25, color='gray', alpha=0.7, edgecolor='black')#, density=True)

        # Clear the previous histogram
        axes[i].cla()

        # Plot the histogram with colored bins
        for count, edge in zip(hist_data, bins):
            axes[i].bar(edge, count, width=(bins[1] - bins[0]), color=cmap(norm(edge)), edgecolor='black', alpha=0.7)

        axes[i].set_xlabel(name)
        axes[i].set_ylabel('Frequency')
        axes[i].grid(True, which='both', linestyle='--', linewidth=0.5)
        axes[i].set_axisbelow(True)

        if log_scale:
            axes[i].set_yscale('log')

    plt.show()
    plt.close()
    



def match_array_shape(imd_arr, lst_arr, scaling_factor=7):

    '''bring the arrays to the same shape.
    Resamples IMD, repeats LST.
    '''

    # resize IMD to shape divisible by scaling_factor
    zoom_factors = (scaling_factor*lst_arr.shape[0]/imd_arr.shape[0], scaling_factor*lst_arr.shape[1]/imd_arr.shape[1])

    # Resample imd_window to 7*lst_arr.shape[0] x 7*lst_arr.shape[1]
    # order=1 for bilinear interpolation
    imd_arr_reshaped = zoom(imd_arr, zoom_factors, order=1) 
    
    # convert to int
    imd_arr_reshaped[np.isnan(imd_arr_reshaped)] = 255 
    imd_arr_reshaped = imd_arr_reshaped.astype(int)
    
    # convert back to float
    imd_arr_reshaped = imd_arr_reshaped.astype(float)
    imd_arr_reshaped[imd_arr_reshaped == 255] = np.nan
    

    # repeat LST on both axis
    lst_arr_reshaped = np.repeat(np.repeat(lst_arr, scaling_factor, axis=0), scaling_factor, axis=1)
    
    return imd_arr_reshaped, lst_arr_reshaped



    
def generate_scatter_plot(chosen_region, imd_layer_name, lst_layer_name, filter_outliers=True, exclude_values=[0,100], log_scale=False):

    # Initialize lists to store IMD values and corresponding mean LST values
    imd_values = []
    lst_mean_values = []


    output = read_image(chosen_region, 'IMD')
    imd_arr, imd_arr_min, imd_arr_max = output['array'], output['min_value'], output['max_value']

    output = read_image(chosen_region, 'LST')
    lst_arr, lst_arr_min, lst_arr_max = output['array'], output['min_value'], output['max_value']


    imd_arr, lst_arr = match_array_shape(imd_arr, lst_arr, scaling_factor=7)
    # print(imd_arr.shape, lst_arr.shape)
    # np.unique(imd_arr)

    # Get unique IMD values, excluding NaNs
    unique_imd_values = np.unique(imd_arr[~np.isnan(imd_arr)])
    # print(unique_imd_values)

    # Iterate over each unique IMD value
    for imd_val in unique_imd_values:

        # Find the corresponding LST values
        corresponding_lst_values = lst_arr[imd_arr == imd_val]
        
        # Calculate the mean of the corresponding LST values
        mean_lst_val = np.nanmean(corresponding_lst_values)
        
        # Append the values to the lists
        imd_values.append(imd_val)
        lst_mean_values.append(mean_lst_val)
        
        
    # Convert lists to numpy arrays for easier manipulation
    imd_values_np = np.array(imd_values)
    lst_mean_values_np = np.array(lst_mean_values)
    
    if filter_outliers:
        # Calculate the IQR for lst_mean_values
        Q1 = np.percentile(lst_mean_values_np, 25)
        Q3 = np.percentile(lst_mean_values_np, 75)
        IQR = Q3 - Q1

        # Define the bounds for outliers
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Filter out the outliers
        filtered_indices = (lst_mean_values_np >= lower_bound) & (lst_mean_values_np <= upper_bound)
        filtered_imd_values = imd_values_np[filtered_indices]
        filtered_lst_mean_values = lst_mean_values_np[filtered_indices]
    else:
        filtered_imd_values = imd_values_np
        filtered_lst_mean_values = lst_mean_values_np
        
    # remove 0 and 100 values
    # remove masked values
    for mask_value in exclude_values:
        filtered_indices = filtered_imd_values != mask_value
        filtered_imd_values = filtered_imd_values[filtered_indices]
        filtered_lst_mean_values = filtered_lst_mean_values[filtered_indices]
            
        # filtered_lst_mean_values = filtered_lst_mean_values[(filtered_imd_values != 0) & (filtered_imd_values != 100)]  
        # filtered_imd_values = filtered_imd_values[(filtered_imd_values != 0) & (filtered_imd_values != 100)]

    # Create a scatter plot without outliers
    plt.figure(figsize=(8, 6))
    plt.scatter(filtered_imd_values, filtered_lst_mean_values, c=filtered_lst_mean_values, cmap='Spectral_r', marker='o', s=100, edgecolors='black')
    plt.xlabel(imd_layer_name)
    plt.ylabel(f'Mean {lst_layer_name}')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    if log_scale:
        plt.yscale('log')
        
    plt.show()
    plt.close()
    
    
def calculate_statistics_masked(arr, exclude_values):
    
    masked_arr = arr[~np.isin(arr, exclude_values)].flatten()
    
    mean_val = np.nanmean(masked_arr)
    median_val = np.nanmedian(masked_arr)
    percentile_90_val = np.nanpercentile(masked_arr, 90)

    return mean_val, median_val, percentile_90_val







def analyze_masked_area(chosen_region, mask_below, clim, imd_layer_name, lst_layer_name, mask_by='LST'):
    
    
    from folium.plugins import SideBySideLayers

    m = folium.Map(location=(30, 20), zoom_start=4)

    layer_right = folium.TileLayer('openstreetmap')
    layer_left = folium.TileLayer('cartodbpositron')

    sbs = folium.plugins.SideBySideLayers(layer_left=layer_left, layer_right=layer_right)

    layer_left.add_to(m)
    layer_right.add_to(m)
    sbs.add_to(m)

    m


    # Create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    map = folium.Map(location=coordinates, zoom_start=regions_dict[chosen_region][1])

    figure = folium.Figure(width=600, height=400)
    map = folium.Map(coordinates, zoom_start=regions_dict[chosen_region][1], tiles='Cartodb Positron').add_to(figure)

    output = read_image(chosen_region, 'IMD')
    imd_arr, imd_arr_min, imd_arr_max = output['array'], output['min_value'], output['max_value']

    output = read_image(chosen_region, 'LST')
    lst_arr, lst_arr_min, lst_arr_max, bounds = output['array'], output['min_value'], output['max_value'], output['bounds']

    imd_arr, lst_arr = match_array_shape(imd_arr, lst_arr, scaling_factor=7)

    if mask_by == 'LST':
        mask = np.where(lst_arr<mask_below)
    elif mask_by == 'IMD':
        mask = (imd_arr < mask_below) | np.isnan(imd_arr) | (imd_arr == 255)
    else:
        raise ValueError('Invalid mask_by argument. Choose from "LST" or "IMD".')
        
    lst_arr[mask] = np.nan
    imd_arr[mask] = np.nan


    # plt.imshow(lst_arr, cmap='Spectral_r')
    # plt.clim(clim)

    os.makedirs('tmp', exist_ok=True)
    path_to_lst_png = f'tmp/tmp_masked_LST.png'
    save_as_png(lst_arr, path_to_lst_png, color_code='Spectral_r', clim=clim)

    # plt.imshow(imd_arr, cmap='Reds')
    # plt.clim(0,100)

    path_to_imd_png = f'tmp/tmp_masked_IMD.png'
    save_as_png(imd_arr, path_to_imd_png, color_code='Reds', clim=(0,100))


    imd_map_setup = {'path': path_to_imd_png, 'layer_name': imd_layer_name, 'color_code': 'Greys', 'opacity': 1, 'folium_color': None, 'reverse': False, 'min_value': imd_arr_min, 'max_value': imd_arr_max}
    lst_map_setup = {'path': path_to_lst_png, 'layer_name': lst_layer_name, 'color_code': 'Spectral_r', 'opacity': 1, 'folium_color': 'Spectral_04', 'reverse': True, 'min_value': clim[0], 'max_value': clim[1]}

    for setup in [imd_map_setup, lst_map_setup]:
        
        path_to_png = setup['path']
        layer_name = setup['layer_name']
        color_code = setup['color_code']
        opacity = setup['opacity']
        folium_color = setup['folium_color']
        reverse = setup['reverse']
        min_value = setup['min_value']
        max_value = setup['max_value']


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

     
    

