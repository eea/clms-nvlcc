import os
import folium
import branca.colormap as cm
from IPython.display import display, HTML
import numpy as np

from modules.utils import define_colormap
from modules.regions_dict import regions_dict
from modules.images import read_image, save_as_png
from modules.analysis import match_array_shape





def show_on_map(rasters_dir, chosen_region, base_map, set_dataset_properties):
    
    # Create a folium map centered around the chosen region
    coordinates = regions_dict[chosen_region][0]
    map = folium.Map(location=coordinates, zoom_start=regions_dict[chosen_region][1])

    figure = folium.Figure(width=600, height=400)
    map = folium.Map(coordinates, zoom_start=regions_dict[chosen_region][1], tiles=base_map).add_to(figure)
    
    
    for ds_properties in set_dataset_properties:
    
        dataset_label, layer_name, color_code, folium_color, reverse, opacity = ds_properties['label'], ds_properties['layer_name'], ds_properties['color_code'], ds_properties['folium_color'], ds_properties['reverse'], ds_properties['opacity']
    
        dataset_dict = read_image(rasters_dir, chosen_region, dataset_label)
        arr, bounds, arr_min, arr_max = dataset_dict['array'], dataset_dict['bounds'], dataset_dict['min_value'], dataset_dict['max_value']
        
        os.makedirs('tmp', exist_ok=True)
        path_to_png = f'tmp/tmp_{dataset_label}.png'
        save_as_png(arr, path_to_png, color_code=color_code)

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
            colormap = define_colormap(folium_color, arr_min, arr_max, reverse)
            map.add_child(colormap)

    folium.LayerControl().add_to(map)
    
    return map


def display_side_by_side(m1, m2):  # TBD!!! use DualMap instead??
    '''
    Display two folium maps side by side.
    '''

    htmlmap = HTML('<iframe srcdoc="{}" style="float:left; width: {}px; height: {}px; display:inline-block; width: 49%; margin: 0 auto; border: 2px solid black"></iframe>'
            '<iframe srcdoc="{}" style="float:right; width: {}px; height: {}px; display:inline-block; width: 49%; margin: 0 auto; border: 2px solid black"></iframe>'
            .format(m1.get_root().render().replace('"', '&quot;'),500,500,
                    m2.get_root().render().replace('"', '&quot;'),500,500))
    display(htmlmap)
    
    
    
    
