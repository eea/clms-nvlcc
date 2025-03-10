# Urban Heat Island Detection with CLMS HRL Imperviousness Data

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/eea/clms-nvlcc/HEAD?urlpath=%2Fdoc%2Ftree%2Fuhi_detection_with_clms_imperviousness.ipynb)

## Overview

This repository contains a Jupyter Notebook and accompanying scripts used for detecting and analyzing Urban Heat Islands (UHIs) using the CLMS HRL Imperviousness Density 2021 dataset. The analysis investigates the correlation between artificial surface sealing and elevated land surface temperatures, demonstrating how urbanization contributes to localized heating effects.

## Features
- Exploration of UHIs across different cities in Austria.
- Visualization of imperviousness and land surface temperature datasets.
- Interactive maps and visualizations to identify UHIs.
- Statistical analysis to quantify the relationship between imperviousness and surface temperature.

## Getting Started
Launch the notebook directly using Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/eea/clms-nvlcc/HEAD?urlpath=%2Fdoc%2Ftree%2Fuhi_detection_with_clms_imperviousness.ipynb)

Or clone the repository and run it locally:

```
git clone https://github.com/eea/clms-nvlcc.git
cd clms-nvlcc
jupyter notebook
```

## Repository Structure
`uhi_detection_with_clms_imperviousness.ipynb` – main notebook for UHI analysis.

`modules/` – directory with supporting Python modules for visualization and analysis.

`aoi_rasters/` – directory with imperviousness and land surface temperature datasets cropped to areas of interest used in the analysis.

`datasets/` – directory with Austria-wide imperviousness and land surface temperature datasets.

