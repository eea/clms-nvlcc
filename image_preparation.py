
import os
import rasterio
import subprocess
from osgeo import ogr


def reproject_by_template(raster_in, template_file, raster_out, target_res, resampling_method = 'nearest',
                          use_src_nodata = False, target_no_data=None, additional_arguments = '', capture_output=True):
    
    '''
    Reproject and resample image to the template image.
    - Input: 
            raster_in: image to be reprojected
            raster_out: output path
            template_file: image based on which to do the reprojection
            target_res: target resolution of the output image
            use_src_nodata: if True, -srcnodata src.nodata is passed to gdalwarp
            target_no_data: if not none, -dstnodata target_no_data is passed to gdalwarp
            additional_arguments: more arguments to pass to GDAL. It is expected as a single string
            capture_output: if set to True, the output od the subprocess comand will NOT be printed
    '''
    
    # obtain bounds from the template_file
    with rasterio.open(template_file) as src:
        target_projection = str(src.crs)
        bounds = src.bounds # left bottom right top
        x_res, y_res = src.res
        src_no_data = src.nodata
    
    ulx = min(bounds[0], bounds[2])  # ulx / xmin
    lrx = max(bounds[0], bounds[2])  # lrx / xmax
    uly = max(bounds[1], bounds[3])  # uly / ymax
    lry = min(bounds[1], bounds[3])  # lry / ymin    
    
    # parse additional_arguments string
    if len(additional_arguments) > 0:
        additional_arguments_parsed = additional_arguments.split(' ')
    else:
        additional_arguments_parsed = []
        
    if use_src_nodata == True:
        additional_arguments_parsed += ['-srcnodata', str(src_no_data)]
        
    if target_no_data is not None:
        additional_arguments_parsed += ['-dstnodata', str(target_no_data)]
    
    # GDAL reprojection command
    cmd = ['gdalwarp'] + additional_arguments_parsed + [
                        # '-srcnodata', str(src_no_data), '-dstnodata', str(target_no_data),
                        '-tr', str(target_res), str(target_res), 
                        '-te', str(ulx), str(lry), str(lrx), str(uly),
                        '-t_srs', target_projection, 
                        '-r', resampling_method, 
                        '-of','GTiff', 
                        '-co', 'compress=LZW', 
                        raster_in, raster_out
                        ]    
    
    subprocess.run(cmd, capture_output=capture_output)
    

def rasterize_shapefile(input_image, output_image, target_res, capture_output=True):
        
        '''
        Rasterize input_image (.shp file) to the specified resolution target_res.
        The output raster has two values: 1=insitde shapefiles, 0=outside shapefiles
        Save output raster to output_image.
        capture_output: if set to True, the output od the subprocess comand will NOT be printed
        '''
        
        # Open the data source and read in the extent
        source_ds = ogr.Open(input_image)
        source_layer = source_ds.GetLayer()
        x_min, x_max, y_min, y_max = source_layer.GetExtent()
        source_srs = source_layer.GetSpatialRef()
        source_ds = None
        
        x_res = int((x_max - x_min) / target_res)
        y_res = int((y_max - y_min) / target_res)      
        
        command = [
            'gdal_rasterize',
            '-te', str(x_min), str(y_min), str(x_max), str(y_max),
            '-ts', str(x_res), str(y_res),
            '-ot', 'Byte',
            '-of', 'GTiff',
            '-co', 'COMPRESS=LZW',
            '-init', '0',
            '-burn', '1',
            input_image, output_image
        ]
        subprocess.run(command, capture_output=capture_output)


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
    

##############################################################################################################
# reproject LST and IMD to 3857/4326
##############################################################################################################

# # target_res = 70

# path_to_lst = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/LST_composites/2023_LST_AT_merged_composite_mean_70m_3035.tif'
# path_to_imd = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/IMD/CLMS_HRLNVLCC_IMD_S2021_R10m_AT_3035_V1_R0_20230731.tif'

# template_path = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2406_for_heatadapt_delivery/01_AT_LST_composite/tmp/AT_LST_mean_composite_S2022_2023_R70m_3857.tif'

# path_to_lst_reprojected = path_to_lst.replace('3035.tif', '3857.tif')
# path_to_imd_reprojected = path_to_imd.replace('_3035_', '_3857_')
# print(path_to_lst_reprojected)
# print(path_to_imd_reprojected)

# reproject_by_template(path_to_lst, template_path, path_to_lst_reprojected, 70, use_src_nodata=True, capture_output=False)
# reproject_by_template(path_to_imd, template_path, path_to_imd_reprojected, 10, use_src_nodata=True, capture_output=False)


##############################################################################################################
# rasterize region shapefiles
##############################################################################################################

# path_to_shapefile_folder = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/region_shapefiles/'
# output_folder = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/region_shapefiles/rasterized_3035/'

# files_to_rasterize = list_filepaths(path_to_shapefile_folder, ['.shp'], ['.aux'])
# for f in files_to_rasterize:
#     print(f)
    

# for f in files_to_rasterize:
        
#     print('\nProcessing:', f)
#     output_name = os.path.basename(f).split('.')[0] + '.tif'
#     output_path = os.path.join(output_folder, output_name)
#     tmp_path = os.path.join(output_folder, 'tmp.tif')

#     if not os.path.exists(output_path):
#         rasterize_shapefile(f, tmp_path, target_res, capture_output=False)
#         reproject_by_template(tmp_path, path_to_lst, output_path, target_res, capture_output=False)
#         os.remove(tmp_path)
#     else:
#         print('Output file already exists:', output_path)
        



##############################################################################################################
# cut LST and IMD to shp regions
##############################################################################################################

target_proj = 'EPSG:4326'
target_res = 70

  
path_to_lst = f'/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/LST_composites/2023_LST_AT_merged_composite_mean_70m_{target_proj.split(":")[1]}.tif'
# path_to_lst = f'/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/IMD/CLMS_HRLNVLCC_IMD_S2021_R10m_AT_{target_proj.split(":")[1]}_V1_R0_20230731.tif'
path_to_shapefile_folder = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/region_shapefiles/'

output_folder = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/region_rasters/'
if not os.path.exists(output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
# template_raster = os.path.join(output_folder, 'template.tif')
    
shp_files = list_filepaths(path_to_shapefile_folder, ['.shp'], ['.aux'])
for f in shp_files:
    print(f)
    
 
for shp in shp_files:
# shp = '/mnt/ongoing/processing/2788_HeatMon/02_Interim_Products/2412_NVLCC_IMD_use_case/region_shapefiles/BEV_VGD_Bundeslaender_NiederOesterreich.shp'
    print('\nClipping to:', shp)
    shp_filename = os.path.basename(shp).split('.')[0]
    output_name = os.path.basename(path_to_lst).split('.')[0]+'_'+shp_filename.split('_')[-1] + '.tif'
    output_path = os.path.join(output_folder, output_name)
    tmp_path = os.path.join(output_folder, 'tmp.tif')

    if not os.path.exists(output_path):
        # clip to AT boundary
        subprocess.run(['gdalwarp', '-overwrite', 
                        '-t_srs', target_proj,
                        '-of',  'GTiff', 
                        '-cutline', shp, '-cl', shp_filename, '-crop_to_cutline', 
                        '-co', 'compress=LZW', 
                        path_to_lst, output_path],capture_output=False)
        
        # reproject_by_template(tmp_path, template_raster, output_path, target_res, resampling_method = 'average', capture_output=False)
        
        # os.remove(tmp_path)
        
    else:
        print('Output file already exists:', output_path)
        
