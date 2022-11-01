# CDE_wind_data_processing

## How to use data processing

for first time running, please run `install.bat` file

To get the data from DeltaOhm and process them, use either:
 - `run_hide-browser.bat`: the scraping process will not be shown in a browser, the whole process will run in the background
 - `run_show-browser.bat`: a browser will be shown running the scraping process, the rest of the processes will run in the background


## How to use ARCGIS code (work in progress)

for first time installation, open an anaconda prompt, run this line of code:

> conda install -c esri arcgis

you must also have arcgis pro installed on your computer i think

you can then run `update-arcgis-data.ipynb` in jupyter-notebook (with anaconda environment that has arcgis installed)