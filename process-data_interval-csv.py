from copy import copy
from datetime import datetime, timedelta
import os
import shutil
import csv
from zipfile import ZipFile
from collections import OrderedDict

from CONSTANTS import ARCGIS_TIME_FORMAT, DATA_COL_IGNORE, DATA_COL_REPLACE, DOWNLOADED_TIME_FORMAT, EXTRACT_DIRECTORY, INFO_COL_REPLACE, PROCESSED_DATA_DIRECTORY, STATION_DATA_FILE, ZIP_DIRECTORY

###############################################################################
# global constants & preprocessing


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


    stats_headers = []
    stats = {}
    if os.path.isfile(f):
        new_processed_data_files = {} # a dictionary of the newly processed csv files

        # read each extracted csv file 
        with open(f, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            file_field_replace = {}
            
            # -------------------------------------
            # add the station data headers (wind speed, wind direction, etc...)
            for field_name in reader.fieldnames: # go through each data field name in the csv file
                check = False # here all field names are to be replaced, this check is to detect whether there's a field not present in the above dictionary
                field_name_lowercase = field_name.lower() # check the field name in lowercase
                for matching_field_name in DATA_COL_REPLACE: # iterate through the replace list above
                    if matching_field_name in field_name_lowercase: # check if field name match
                        check = True
                        if (matching_field_name in DATA_COL_IGNORE): break
                        file_field_replace[field_name] = DATA_COL_REPLACE[matching_field_name]
                        if DATA_COL_REPLACE[matching_field_name] not in data_headers:
                            data_headers.append(DATA_COL_REPLACE[matching_field_name])
                        break
                if not check:
                    print('not matched field name:', field_name) # print a warning if the field name replacement string cannot be found

            # ===========================================================
            # process the csv file data
            full_day_data_file = []
            for row in reader: # go through each row in the csv file
                # -------------------------------------
                # get the row timestamp and classify it into the corresponding 15 min file
                # also update the timestamp with the output format (no change at the moment)
                row_time = datetime.strptime(row['Timestamp'], DOWNLOADED_TIME_FORMAT)
                interval_id = {
                    '15min': (row_time - timedelta(minutes=row_time.minute % 15, seconds=row_time.second)).strftime(ARCGIS_TIME_FORMAT),
                    '1hour': (row_time - timedelta(hours=1, minutes=row_time.minute, seconds=row_time.second)).strftime(ARCGIS_TIME_FORMAT)
                }

                # -------------------------------------
                # add the row data (wind speed, wind direction, etc...)
                for field_name in reader.fieldnames:
                    if field_name not in file_field_replace: continue
                    for i in interval_id:
                        if station_id not in aggregated_data[i]:
                            aggregated_data[i][station_id] = {}
                        if interval_id[i] not in aggregated_data[i][station_id]:
                            aggregated_data[i][station_id][interval_id[i]] = OrderedDict()
                        display_field_name = file_field_replace[field_name]
                        if display_field_name not in aggregated_data[i][station_id][interval_id[i]]:
                            aggregated_data[i][station_id][interval_id[i]][display_field_name] = []
                        try:
                            aggregated_data[i][station_id][interval_id[i]][display_field_name].append(float(row[field_name]))
                        except ValueError:
                            pass



print('_ processing data')
new_files = {}
for interval in ['15min', '1hour']:
    full_data_interval = []
    full_data_header = copy(station_info_headers)
    full_data_rows = []
    full_data_header.append('Timestamp')
    for header in data_headers:
        full_data_header.append(header)
    for station in station_ids:
        row_data = []
        station_info = station_data[station]
        for field_name in station_info:
            row_data.append(station_info[field_name])
        for timestamp in aggregated_data[interval][station]:
            time_data = aggregated_data[interval][station][timestamp]
            time_row_data = copy(row_data)
            time_row_data.append(timestamp)
            for field_name in data_headers:
                avg_val = 0
                if len(time_data[field_name]) > 0:
                    avg_val = sum(time_data[field_name]) / len(time_data[field_name])
                time_row_data.append(avg_val)
            full_data_rows.append(time_row_data)
    
    new_files['interval_' + interval + '_All.csv'] = [full_data_header] + full_data_rows

    # df=pd.read_excel(file)
    # station_no=file.replace('_WR.xlsx','')
    # image_name=file.replace('_WR.xlsx','.png')
    # new=df.dropna()
    # ax = WindroseAxes.from_ax()
    # ax.bar(new['Wind direction'], new['Wind speed'], normed=True, opening=0.8, edgecolor='white')
    # ax.set_xticklabels(['E', 'NE', 'N', 'NW',  'W', 'SW', 'S', 'SE'])
    # ax.set_title(station_no)
    # ax.set_legend()
    # plt.savefig(image_name)
# ===========================================================
# write each of the file in the file list as csv
print('_ writing to csv')
for file_name in new_files:
    with open(PROCESSED_DATA_DIRECTORY + '/' + file_name, 'w', newline='', encoding='UTF8') as f:
        print('    writing file:', file_name)
        writer = csv.writer(f)
        for row in new_files[file_name]:
            writer.writerow(row)

###############################################################################
# remove redundant data files
shutil.rmtree(EXTRACT_DIRECTORY) # remove the extracted csv files
# shutil.rmtree(ZIP_DIRECTORY)     # remove the downloaded zip files
