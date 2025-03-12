'''
This module contains functions for analyzing the data and generating plots.
'''

import matplotlib
import matplotlib.pyplot as plt
import numpy as np  

from modules.images import read_image, match_array_shape


def calculate_statistics(rasters_dir, chosen_region, dataset_label, exclude_values=[]):
    '''
    Calculate the statistics of the selected dataset over the chosen region.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters
    - `chosen_region (str)`: name of the region to be analyzed. 
            Used to identify the right region images in `rasters_dir`.
    - `dataset_label (str)`: label of the dataset to be analyzed 
            (`'IMD'` for imperviousness, `'LSM'` for land surface temperature).
            Used to identify the dataset in `rasters_dir`.
    - `exclude_values (list)`: list of values to be excluded from the analysis. 
            Default is `[]`.
            
    Output:
    - dictionary with the following keys:
        - `'mean' (float)`: mean value of the dataset
        - `'median' (float)`: median value of the dataset
        - `'percentile_90' (float)`: 90th percentile of the dataset
        - `'min' (float)`: minimum value of the dataset
        - `'max' (float)`: maximum value of the dataset
    '''
    
    # raed the dataset into an array
    arr = read_image(rasters_dir, chosen_region, dataset_label)['array']    
    
    # mask the values to be excluded
    masked_arr = arr[~np.isin(arr, exclude_values)].flatten()
    
    # calculate the statistics
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


def calculate_statistics_masked(arr, exclude_values):
    '''
    Calculate the mean, median, and 90th percentile of the array, excluding specified values.
    
    Input:
    - `arr (np.array)`: array to be analyzed
    - `exclude_values (list)`: list of values to be excluded from the analysis
    
    Output:
    - `mean_val (float)`: mean value of the array
    - `median_val (float)`: median value of the array
    - `percentile_90_val (float)`: 90th percentile of the array
    '''
    
    masked_arr = arr[~np.isin(arr, exclude_values)].flatten()
    
    mean_val = np.nanmean(masked_arr)
    median_val = np.nanmedian(masked_arr)
    percentile_90_val = np.nanpercentile(masked_arr, 90)

    return mean_val, median_val, percentile_90_val



def plot_histograms(rasters_dir, chosen_region, histogram_setups, 
                        figure_size=(12, 4), num_bins=25, log_scale=False):
    
    '''
    Plot histograms of multiple datasets over the chosen region.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters
    - `chosen_region (str)`: name of the region to be analyzed. 
            Used to identify the right region images in `rasters_dir`.
    - `histogram_dicts (list)`: list of dictionaries with the desired properties of each histogram.
        Each dictionary should contain the following keys:
        - `label (str)`: label of the dataset (`'IMD'` for imperviousness, `'LSM'` for land surface temperature).
        - `layer_name (str)`: label to be displayed on the histogram
        - `color_code (str)`: color code to be used for the histogram
        - `exclude_values (list)`: list of values to be excluded from the plot
        - 'title (str)`: title for the histogram
    - `figure_size (tuple)`: size of the figure. Default is `(12, 4)`.
    - `bins (int)`: number of bins for the histogram. Default is `25`.
    - `log_scale (bool)`: whether to use log scale for the y-axis. Default is `False`.
    
    Output: none
    '''

    fig, axes = plt.subplots(1, len(histogram_setups), figsize=figure_size)
    axes = np.atleast_1d(axes)  # Ensure axes is always an array

    for i, hist_setup in enumerate(histogram_setups):
                                
        label, name, color, exclude_values, title = (
            hist_setup['label'],
            hist_setup['layer_name'],
            hist_setup['color_code'],
            hist_setup['exclude_values'],
            hist_setup['title']
        )

        output = read_image(rasters_dir, chosen_region, label)
        arr, arr_min, arr_max = output['array'], output['min_value'], output['max_value']

        # Normalize the data for color mapping
        norm = plt.Normalize(vmin=arr_min, vmax=arr_max)
        cmap = matplotlib.colormaps.get_cmap(color)

        # Get the histogram data
        hist_data, bins, _ = axes[i].hist(arr[~np.isin(arr, exclude_values)].flatten(), 
                                        bins=num_bins, color='gray', alpha=0.7, edgecolor='black')

        # Clear the previous histogram
        axes[i].cla()

        # Plot the histogram with colored bins
        for count, edge in zip(hist_data, bins):
            axes[i].bar(edge, count, width=(bins[1] - bins[0]), color=cmap(norm(edge)), 
                                        edgecolor='black', alpha=0.7)

        axes[i].set_xlabel(name)
        axes[i].set_ylabel('Frequency')
        axes[i].grid(True, which='both', linestyle='--', linewidth=0.5)
        axes[i].set_axisbelow(True)
        axes[i].set_title(f'{chosen_region}, AT: {title}')

        if log_scale:
            axes[i].set_yscale('log')

    plt.show()
    plt.close()
    

def generate_scatter_plot(rasters_dir, chosen_region, imd_layer_name, lst_layer_name, 
            filter_outliers=True, exclude_values=[0,100], figure_size=(8, 6), log_scale=False):
    '''
    Generate a scatter plot of the mean LST values against the IMD values for the chosen region.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters
    - `chosen_region (str)`: name of the region to be analyzed. 
            Used to identify the right region images in `rasters_dir`.
    - `imd_layer_name (str)`: name of the IMD layer to be displayed
    - `lst_layer_name (str)`: name of the LST layer to be displayed
    - `filter_outliers (bool)`: whether to filter out the outliers. Default is `True`.
    - `exclude_values (list)`: list of values to be excluded from the analysis. Default is `[0, 100]`.
    - `figure_size (tuple)`: size of the figure. Default is `(8, 6)`.
    - `log_scale (bool)`: whether to use log scale for the y-axis. Default is `False`.
    
    Output: none
    '''

    # initialize lists to store IMD values and corresponding mean LST values
    imd_values = []
    lst_mean_values = []

    # read IMD and LST rasters into arrays
    im_dict = read_image(rasters_dir, chosen_region, 'IMD')
    imd_arr = im_dict['array']

    im_dict = read_image(rasters_dir, chosen_region, 'LST')
    lst_arr = im_dict['array'] 

    # match the shape of the two arrays
    imd_arr, lst_arr = match_array_shape(imd_arr, lst_arr, scaling_factor=7)

    # get unique IMD values, excluding nans
    unique_imd_values = np.unique(imd_arr[~np.isnan(imd_arr)])

    # calculate mean LST for each IMD value
    for imd_val in unique_imd_values:
        corresponding_lst_values = lst_arr[imd_arr == imd_val]
        mean_lst_val = np.nanmean(corresponding_lst_values)
        
        # append to lists
        imd_values.append(imd_val)
        lst_mean_values.append(mean_lst_val)
        
    # convert lists to numpy arrays for easier manipulation
    imd_values_np = np.array(imd_values)
    lst_mean_values_np = np.array(lst_mean_values)
    
    if filter_outliers:
        # calculate interquartile range
        q1 = np.percentile(lst_mean_values_np, 25)
        q3 = np.percentile(lst_mean_values_np, 75)
        iqr = q3 - q1

        # define bounds for outliers
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # filter out the outliers
        filtered_indices = (lst_mean_values_np >= lower_bound) & (lst_mean_values_np <= upper_bound)
        filtered_imd_values = imd_values_np[filtered_indices]
        filtered_lst_mean_values = lst_mean_values_np[filtered_indices]
    else:
        filtered_imd_values = imd_values_np
        filtered_lst_mean_values = lst_mean_values_np
        
    # exclude specified values from the analysis
    for mask_value in exclude_values:
        filtered_indices = filtered_imd_values != mask_value
        filtered_imd_values = filtered_imd_values[filtered_indices]
        filtered_lst_mean_values = filtered_lst_mean_values[filtered_indices]

    # create and configure scatter plot
    plt.figure(figsize=figure_size)
    plt.scatter(filtered_imd_values, filtered_lst_mean_values, 
                c=filtered_lst_mean_values, 
                cmap='Spectral_r', 
                marker='o', 
                s=100, 
                edgecolors='black')
    plt.xlabel(imd_layer_name)
    plt.ylabel(f'Mean {lst_layer_name}')
    plt.title(f'{chosen_region}, AT: relationship between IMD and LST')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    if log_scale:
        plt.yscale('log')
        
    plt.show()
    plt.close()