'''
This module contains functions for reading and visualizing raster datasets.
'''

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image
from scipy.ndimage import zoom

from modules.utils import list_filepaths
from modules.regions_dict import regions_dict


def visualize_datasets(dataset_dicts, figure_size=(12, 6)):
    '''
    Matplotlib visualization of raster datasets.
    
    Input:
    - `dataset_dicts (list)`: list of dictionaries with properties of the datasets to be displayed.
        Each dictionary should contain the following keys:
        - `path (str)`: path to the raster file to be displayed
        - `color (str)`: color code to be used for the plot
        - `plot_label (str)`: label to be displayed on the plot
        - `colorbar_label (str)`: label to be displayed on the colorbar
        - `clim (tuple)`: min and max values for the color scale
    - `figure_size (tuple)`: size of the figure. Default is `(12, 6)`.
    
    Output: none
    '''

    fig, axes = plt.subplots(1, len(dataset_dicts), figsize=figure_size)
    axes = np.atleast_1d(axes)  # Ensure axes is always an array
    
    for i, prop in enumerate(dataset_dicts):
    
        path, color, name, lbl, clim = (
            prop['path'], 
            prop['color'], 
            prop['plot_label'], 
            prop['colorbar_label'], 
            prop['clim']
        )
    
        # read the dataset into array
        with rasterio.open(path) as src:
            arr = src.read(1)
            nodata = src.nodata
            
        # mask nodata values
        arr = arr.astype(float)
        arr[arr == nodata] = float('nan')
        
        # configure the plot
        im = axes[i].imshow(arr, cmap=color)
        axes[i].set_title(name)
        axes[i].set_xticks([])
        axes[i].set_yticks([])
        im.set_clim(clim)
        cbar = fig.colorbar(im, ax=axes[i], orientation='horizontal')
        cbar.set_label(lbl)
        arr = None

    plt.show()
    plt.close()
    
    return


def read_image(rasters_dir, chosen_region, dataset_label, target_projection = '4326', mask_below=None):    
    '''
    Read raster into an array.
    
    Input:
    - `rasters_dir (str)`: path to the directory with rasters
    - `chosen_region (str)`: name of the region to be displayed.
            Used to identify the right region images in `rasters_dir`. 
    - `dataset_label (str)`: label of the dataset to be displayed 
            (`'IMD'` for imperviousness, `'LSM'` for land surface temperature).
            Used to identify the dataset in `rasters_dir`.
    - `mask_below (float)`: mask values below this threshold. 
            If `None`, no masking is applied. Default is `None`.
    - `target_projection (str)`: target projection of the raster. Default is `'4326'`.
        
    Output:
    - dictionary with the following keys:
        - `'array' (numpy array)`: array with the raster values
        - `'bounds' (list)`: bounds of the raster, format: `[[bottom, left], [top, right]]`
        - `'min_value' (float)`: minimum value of the raster
        - `'max_value' (float)`: maximum value of the raster
        - `'crs' (str)`: coordinate reference system of the raster
        - `'mask' (numpy array)`: array with the mask of the values below the threshold (if `mask_below` is not `None`)
    '''

    # get the region label from the regions_dict
    region_label = regions_dict[chosen_region][2]
    
    # get the path to the right raster
    path_to_dataset = list_filepaths(rasters_dir, 
        [dataset_label, region_label,  '.tif', target_projection], ['.aux'])[0]

    # read the dataset into array
    with rasterio.open(path_to_dataset) as src:
        arr = src.read(1).astype(np.float32)
        
        # mask nodata values
        arr[arr == src.nodata] = np.nan
        
        # get CRS, bounds, min and max values
        src_crs = src.crs.to_string().upper()
        bounds = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
        arr_min = np.nanmin(arr)
        arr_max = np.nanmax(arr)
        
        # mask values below the threshold if requested
        if mask_below is not None:
            mask = np.where(arr<mask_below)
            arr[mask] = np.nan
        
    # return the dictionary with the raster properties
    output_dict = {
        'array': arr, 
        'bounds': bounds, 
        'min_value': arr_min, 
        'max_value': arr_max, 
        'crs': src_crs
    }
    
    if mask_below is not None:
        output_dict['mask'] = mask
    
    return output_dict


def save_as_png(arr, path, color_code='viridis', clim=None, reverse=False):
    '''
    Save an array as a colored PNG image.
    
    Input:
    - `arr (numpy array)`: array to be saved
    - `path (str)`: path to the output PNG file
    - `color_code (str)`: color code to be used for the dataset. Default is `'viridis'`.
    - `clim (tuple)`: min and max values for the color scale. Default is `None`.
    - `reverse (bool)`: whether to reverse the color code. Default is `False`. 
         
    Output: none
    '''
    
    # normalize array data to the range [0, 1]
    if not clim:
        norm = Normalize(vmin=np.nanmin(arr), vmax=np.nanmax(arr))
    else:
        norm = Normalize(vmin=clim[0], vmax=clim[1])
        
    arr_norm = norm(arr)

    # apply colormap
    colormap = plt.get_cmap(color_code)
    arr_colored = colormap(arr_norm)

    # convert the image to uint8 format
    arr_uint8 = (arr_colored[:, :, :3] * 255).astype(np.uint8)

    # set nan values to be transparent
    arr_uint8_with_alpha = np.dstack((arr_uint8, (~np.isnan(arr) * 255).astype(np.uint8)))

    # save image
    image = Image.fromarray(arr_uint8_with_alpha, mode='RGBA')
    image.save(path)
    
 
def match_array_shape(imd_arr, lst_arr, scaling_factor=7):
    '''
    Helper function to bring the two arrays (`IMD` and `LST`) to the same shape. 

    Input:
    - `imd_arr (np.array)`: array with IMD values (larger array, res=10 m)
    - `lst_arr (np.array)`: array with LST values (smaller, array, res=70 m)
    - `scaling_factor (int)`: Resolution scaling factor between the two arrays. Default is `7`.
    
    If `scaling_factor = 1`, the larger array is rasampled to the shape of the smaller array.
    If `scaling_factor > 1`, both arrays are resized to the shape that is multiple of the smaller array,
    with the following steps:
    
    1. resize and resample the larger array to the closest shape multiple of the smaller array.
    2. repeat the smaller array on both axes to match the shape of the resized larger array.

    Output:
    - `imd_arr_reshaped (np.array)`: reshaped array with IMD values
    - `lst_arr_reshaped (np.array)`: reshaped array with LST values 
    
    Example:
    - `imd_arr.shape: (100, 100)`
    - `lst_arr.shape: (14, 14)`
    ---
    - `scaling_factor: 7`
    - `imd_arr_reshaped.shape: (98, 98)`
    - `lst_arr_reshaped.shape: (98, 98)` 
    ---
    - `scaling_factor: 1`
    - `imd_arr_reshaped.shape: (14, 14)`
    - `lst_arr_reshaped.shape: (14, 14)`  
    '''

    # resize IMD to shape divisible by scaling_factor
    zoom_factors = (
        scaling_factor*lst_arr.shape[0]/imd_arr.shape[0], 
        scaling_factor*lst_arr.shape[1]/imd_arr.shape[1]
    )

    # Resample imd_window to 7*lst_arr.shape[0] x 7*lst_arr.shape[1]
    # order=1 for bilinear interpolation
    imd_arr_reshaped = zoom(imd_arr, zoom_factors, order=1) 
    
    # convert to int
    imd_arr_reshaped[np.isnan(imd_arr_reshaped)] = 255 
    imd_arr_reshaped = imd_arr_reshaped.astype(int)
    
    # convert back to float
    imd_arr_reshaped = imd_arr_reshaped.astype(float)
    imd_arr_reshaped[imd_arr_reshaped == 255] = np.nan
    
    # repeat LST on both axis to match IMD shape
    lst_arr_reshaped = np.repeat(np.repeat(lst_arr, scaling_factor, axis=0), scaling_factor, axis=1)
    
    return imd_arr_reshaped, lst_arr_reshaped