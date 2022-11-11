import os
import shutil
import csv
from zipfile import ZipFile

import pandas as pd
from matplotlib import pyplot as plt
from windrose import WindroseAxes

from CONSTANTS import WINDROSE_COL_IGNORE, EXTRACT_DIRECTORY, INFO_COL_REPLACE, WINDROSE_DATA_DIRECTORY, STATION_DATA_FILE, ZIP_DIRECTORY

# clear the processed data directory of the previous run
try:
    shutil.rmtree(WINDROSE_DATA_DIRECTORY)
except Exception as ex:
    pass
os.mkdir(WINDROSE_DATA_DIRECTORY)


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
        for ignoreCol in WINDROSE_COL_IGNORE:
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
    plt.savefig(WINDROSE_DATA_DIRECTORY + '/' + station_id_short + '.png')

###############################################################################
# remove redundant data files
shutil.rmtree(EXTRACT_DIRECTORY) # remove the extracted csv files
# shutil.rmtree(ZIP_DIRECTORY)     # remove the downloaded zip files
