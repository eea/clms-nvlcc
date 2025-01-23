import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image

from modules.utils import list_filepaths
from modules.regions_dict import regions_dict


#object? 
# object(path)
# object.read_image(), object.save_as_png()
# object.min_value, object.max_value, object.bounds

def visualize_datasets(dataset_properties, figure_size=(12, 6)):
    
    fig, axes = plt.subplots(1, len(dataset_properties), figsize=figure_size)
    axes = np.atleast_1d(axes)  # Ensure axes is always an array
    
    for i, prop in enumerate(dataset_properties):
    
        path = prop['path']
        color = prop['color']
        name = prop['plot_label']
        lbl = prop['colorbar_label']
        clim = prop['clim']
    
        # Open the raster files and read the data
        with rasterio.open(path) as src:
            arr = src.read(1)
            nodata = src.nodata
            
        # Mask the nodata values
        arr = arr.astype(float)
        arr[arr == nodata] = float('nan')
        
        # Plot IMD data
        im1 = axes[i].imshow(arr, cmap=color)
        axes[i].set_title(name)
        # axes[i].axis('off')
        axes[i].set_xticks([])
        axes[i].set_yticks([])
        im1.set_clim(clim)
        cbar = fig.colorbar(im1, ax=axes[i], orientation='horizontal')
        cbar.set_label(lbl)
        arr = None

    plt.show()
    plt.close()
    
    return



def read_image(rasters_dir, chosen_region, dataset_label, mask_below=None):    
    '''
    Read LSM and IMD images for the chosen region.
    Return arrays, bounds, min and max values for both images.
    '''

    image_label = regions_dict[chosen_region][3]
    target_projection = '4326' #'3857'

    path_to_dataset = list_filepaths(rasters_dir, [dataset_label, image_label,  '.tif', target_projection], ['.aux'])[0]

    # print(path_to_dataset)
    
    with rasterio.open(path_to_dataset) as src:
        
        arr = src.read(1).astype(np.float32)
        
        arr[arr == src.nodata] = np.nan
        
        # src_crs = src.crs['init'].upper()
        
        # Updated line to access CRS information
        src_crs = src.crs.to_string().upper()


        min_lon, min_lat, max_lon, max_lat = src.bounds
        bounds_lst = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
        
        arr_min = np.nanmin(arr)
        arr_max = np.nanmax(arr)
        
        if mask_below is not None:
            mask = np.where(arr<mask_below)
            arr[mask] = np.nan
        
    output_dict = {'array': arr, 'bounds': bounds_lst, 'min_value': arr_min, 'max_value': arr_max, 'crs': src_crs}
    
    if mask_below is not None:
        output_dict['mask'] = mask
    
    return output_dict


def save_as_png(arr, path, color_code='viridis', clim=None, reverse=False):
    '''
    Save an array as a colored PNG image.
    '''
    
    # Normalize the image data to the range [0, 1]
    if not clim:
        norm = Normalize(vmin=np.nanmin(arr), vmax=np.nanmax(arr))
    else:
        norm = Normalize(vmin=clim[0], vmax=clim[1])
        
    arr_norm = norm(arr)

    # Apply colormap
    colormap = plt.get_cmap(color_code)
    arr_colored = colormap(arr_norm)

    # Convert the image to uint8 format
    arr_uint8 = (arr_colored[:, :, :3] * 255).astype(np.uint8)

    # Set NaN values to be transparent
    arr_uint8_with_alpha = np.dstack((arr_uint8, (~np.isnan(arr) * 255).astype(np.uint8)))

    # Save the image as a PNG file
    image = Image.fromarray(arr_uint8_with_alpha, mode='RGBA')
    image.save(path)
    
    
def save_as_png_test(arr, path, dpi=300):
    
    fig = plt.figure(figsize=(arr.shape[1]/dpi, arr.shape[0]/dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.imshow(arr, cmap='viridis', vmin=np.nanmin(arr), vmax=np.nanmax(arr))
    fig.savefig(path, dpi=dpi, transparent=True)
    plt.close(fig)
    
    return
    