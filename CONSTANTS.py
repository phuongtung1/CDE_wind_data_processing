######## COMMON ########

STATION_DATA_FILE = 'Locations_REF.csv'
ZIP_DIRECTORY = 'downloaded_data'
EXTRACT_DIRECTORY = '_temp'
PROCESSED_DATA_DIRECTORY = 'processed_data'
WINDROSE_DATA_DIRECTORY = 'windrose_img'

DOWNLOADED_TIME_FORMAT = '%Y/%m/%d %H:%M:%S %z'
ARCGIS_TIME_FORMAT = '%Y/%m/%d %H:%M:%S'

######## update-arcgis-add-remove-feature-data.py ########


######## download-data_playwright.py ########


######## process-data_interval-csv.py & process-data_gen_windrose.py ########

# dictionary for replacing station info headers
INFO_COL_REPLACE = {
    "Latutude DD": "Latitude",
    "Longitude DD": "Longitude"
}

# dictionary for replacing data headers (left side must be all in lower case)
DATA_COL_IGNORE = [
    'timestamp',
    '05 battery voltage user code',
    '06 voltage power supply user code',
    '08 wind direction user code'
]
DATA_COL_REPLACE = {
    'timestamp'                         : 'Timestamp',
    '05 battery voltage user code'      : 'Battery voltage',
    '06 voltage power supply user code' : 'Voltage power supply',
    '07 wind speed user code'           : 'Wind Speed',
    '08 wind direction user code'       : 'Wind Direction',
    '09 temperature pt100 user code'    : 'Temperature',
    '10 relative humidity user code'    : 'Relative Humidity',
    '11 solar radiation user code'      : 'Solar Radiation',
    '12 pm1.0 user code'                : 'PM1.0',
    '13 pm2.5 user code'                : 'PM2.5',
    '14 pm10 user code'                 : 'PM10',
}

WINDROSE_COL_IGNORE = [
    '05 battery voltage user code',
    '06 voltage power supply user code',
    '09 temperature pt100 user code',
    '10 relative humidity user code',
    '11 solar radiation user code',
    '12 pm1.0 user code',
    '13 pm2.5 user code',
    '14 pm10 user code'
]
