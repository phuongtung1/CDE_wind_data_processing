from copy import copy
import os
import shutil
import csv
from zipfile import ZipFile

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from windrose import WindroseAxes

###############################################################################
# global constants & preprocessing

# files and directories
STATION_DATA_FILE = 'Locations_REF.csv'
ZIP_DIRECTORY = 'downloaded_data'
EXTRACT_DIRECTORY = '_temp'
PROCESSED_DATA_DIRECTORY = 'windrose_img'

# time formats
INPUT_TIME_FORMAT = '%Y/%m/%d %H:%M:%S %z'
OUTPUT_TIME_FORMAT = '%Y/%m/%d %H:%M:%S %z'
# FILE_NAME_TIME_FORMAT_15MIN = '%Y-%m-%d_%Hh%Mm'
# FILE_NAME_TIME_FORMAT_1HOUR = '%Y-%m-%d_%Hh'
FILE_NAME_TIME_FORMAT_15MIN = '%d/%m/%Y %H:%M'
FILE_NAME_TIME_FORMAT_1HOUR = '%d/%m/%Y %H:%M'

# dictionary for replacing station info headers
INFO_COL_REPLACE = {
    "Latutude DD": "Latitude",
    "Longitude DD": "Longitude"
}

# dictionary for replacing data headers (left side must be all in lower case)
# DATA_COL_REPLACE = {
#     'timestamp'                         : 'Timestamp',
#     '05 battery voltage user code'      : 'Battery voltage [V]',
#     '06 voltage power supply user code' : 'Voltage power supply [V]',
#     '07 wind speed user code'           : 'Wind Speed [m/s]',
#     '08 wind direction user code'       : 'Wind Direction [deg]',
#     '09 temperature pt100 user code'    : 'Temperature PT100 [°C]',
#     '10 relative humidity user code'    : 'Relative Humidity [%]',
#     '11 solar radiation user code'      : 'Solar Radiation [W/m2]',
#     '12 pm1.0 user code'                : 'PM1.0 [µg/m³]',
#     '13 pm2.5 user code'                : 'PM2.5 [µg/m³]',
#     '14 pm10 user code'                 : 'PM10 [µg/m³]',
# }
DATA_COL_IGNORE = [
    '05 battery voltage user code',
    '06 voltage power supply user code',
    '09 temperature pt100 user code',
    '10 relative humidity user code',
    '11 solar radiation user code',
    '12 pm1.0 user code',
    '13 pm2.5 user code',
    '14 pm10 user code'
]
DATA_COL_REPLACE = {
    'timestamp'                         : 'Timestamp',
    '07 wind speed user code'           : 'Wind Speed',
    '08 wind direction user code'       : 'Wind Direction',
}

# clear the processed data directory of the previous run
try:
    shutil.rmtree(PROCESSED_DATA_DIRECTORY)
except Exception as ex:
    pass
os.mkdir(PROCESSED_DATA_DIRECTORY)


###############################################################################
# read the station data file and compile the info into a dictionary
station_data = {}
station_ids = []
with open(STATION_DATA_FILE, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Station'] == '#10' and row['Latutude DD'] == '1.27504722222222':
            station_data[row['Serial number'] + '_old'] = row
        else:
            station_data[row['Serial number']] = row
            station_ids.append(row['Serial number'])
station_ids.sort()

###############################################################################
# extract zip files into a temporary directory
print('_ extracting zip')
for filename in os.listdir(ZIP_DIRECTORY):
    f = os.path.join(ZIP_DIRECTORY, filename)
    if os.path.isfile(f):
        with ZipFile(f, 'r') as myzip:
            myzip.extractall(EXTRACT_DIRECTORY)


###############################################################################
# read the extracted csv files and processing the data
print('_ reading data')
aggregated_data = {
    '15min': {},
    '1hour': {}
}
station_info_headers = []
for field_name in station_data[station_ids[0]]:
    if field_name in INFO_COL_REPLACE:
        station_info_headers.append(INFO_COL_REPLACE[field_name])
    else:
        station_info_headers.append(field_name)
data_headers = []
for filename in os.listdir(EXTRACT_DIRECTORY):
    f = os.path.join(EXTRACT_DIRECTORY, filename)
    station_id = filename.split('_')[0]
    station_info = station_data[station_id]
    station_id_short = 'S' + station_info['Station'][1:]
    df = pd.read_csv(f)
    droppedCols = []
    for (columnName, columnData) in df.iteritems():
        for ignoreCol in DATA_COL_IGNORE:
            if ignoreCol in columnName.lower():
                droppedCols.append(columnName)
                break


    df = df.drop(droppedCols, axis=1)
    df.columns = ['Timestamp', 'Wind Speed', 'Wind Direction']

    droppedRows = []
    for (rowInd, rowVal) in df.iterrows():
        if rowVal[1] == 'ERR:ERROR' or rowVal[2] == 'ERR:ERROR':
            droppedRows.append(rowInd)
    df = df.drop(droppedRows, axis=0)

    ax = WindroseAxes.from_ax()
    ax.bar(df['Wind Direction'].astype(float), df['Wind Speed'].astype(float), normed=True, opening=1, edgecolor='white')
    ax.set_xticklabels(['E', 'NE', 'N', 'NW',  'W', 'SW', 'S', 'SE'])
    ax.set_title(station_id_short)
    ax.set_legend()
    plt.savefig(PROCESSED_DATA_DIRECTORY + '/' + station_id_short + '.png')

###############################################################################
# remove redundant data files
shutil.rmtree(EXTRACT_DIRECTORY) # remove the extracted csv files
# shutil.rmtree(ZIP_DIRECTORY)     # remove the downloaded zip files
