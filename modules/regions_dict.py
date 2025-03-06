'''This file contains the dictionary of regions that can be selected in the main script.
The key of the dictionary is the name of the region, the value is a list with the following elements:
- the coordinates of region, for the maps (latitude, longitude)
- the default zoom level for the maps
- the name of the region as it appears in the raster filename
'''

regions_dict = {"Vienna": [(48.21, 16.37), 10, 'Wien'],
                "Graz": [(47.07, 15.43), 11, 'Graz'],
                "Linz": [(48.30, 14.28), 11, 'Linz'],
                "Salzburg": [(47.80, 13.03), 11, 'Salzburg'],
                "Innsbruck": [(47.27, 11.39), 11, 'Innsbruck'],
                "Klagenfurt": [(46.63, 14.30), 11, 'Klagenfurt'],
                "Villach": [(46.62, 13.85), 11, 'Villach'],
                "St. Pölten": [(48.20, 15.62), 11, 'StPoelten'],
                "Dornbirn": [(47.37, 9.75), 11, 'Dornbirn'],
                "Bregenz": [(47.50, 9.74), 12, 'Bregenz'],
                "Lienz": [(46.83, 12.76), 12, 'Lienz'],
                "Liezen": [(47.59, 14.23), 12, 'Liezen']
}
