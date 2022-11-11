import csv
import os
import shutil
from playwright.sync_api import expect, sync_playwright
import datetime
import sys

from CONSTANTS import STATION_DATA_FILE, ZIP_DIRECTORY

DATA_COLLECTION_PERIOD__DAYS = 0
DATA_COLLECTION_PERIOD__WEEKS = 1

HEADLESS = False
if len(sys.argv) > 1:
    print('Headless:',sys.argv[1])
    if sys.argv[1] == 'True':
        HEADLESS = True
    elif sys.argv[1] == 'False':
        HEADLESS = False
    else:
        HEADLESS = sys.argv[1]

playwright = sync_playwright().start()

# get the list of ids of the devices of which the data is to be retrieved 
DEVICES = set()
with open(STATION_DATA_FILE, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        DEVICES.add(row['Serial number'])


# remove the files currently in the download directory 
try:
    shutil.rmtree(ZIP_DIRECTORY) 
except Exception:
    pass
os.mkdir(ZIP_DIRECTORY)

browser = playwright.chromium.launch(channel="chrome", headless=HEADLESS)
page = browser.new_page()

# Calculate the time range: 24hr range from the closest 15th minute on the clock before this point in time to 
# the closest 15th minute earlier from now (with the seconds round down to 0 for start time and 59th sec of 
# the last minute for end time).
# e.g.: if the time now is  29/09/22 11:35:29.54321
#       start time:         28/09/22 11:30:00  
#       end time:           29/09/22 11:29:59  
time_now = datetime.datetime.now()
# start time: 24 hours, latest 15th minute, 0 second
start_time = time_now - datetime.timedelta(
    days=DATA_COLLECTION_PERIOD__DAYS,
    weeks=DATA_COLLECTION_PERIOD__WEEKS,                        
    # hours=24,                         
    minutes=time_now.minute % 15,       # current number of minutes modulo 15 => number of minutes after the latest (15*x)th minute
    seconds=time_now.second,            # current number of seconds
    microseconds=time_now.microsecond   # current number of microseconds (not necessary maybe)
)
# end time: latest 15th minute, -1 second
end_time = time_now - datetime.timedelta(
    minutes=time_now.minute % 15,       # current number of minutes modulo 15 => number of minutes after the latest (15*x)th minute
    seconds=time_now.second + 1,        # current number of seconds + 1 => it should go from something like 11:15:00 to 11:14:59
    microseconds=time_now.microsecond   # current number of microseconds (not necessary maybe)
)

# get string representations of the start time and end time, each should be a list of 2 strings:
#   1st string: day/month/year (with the year in short format) e.g. 20/09/22
#   2nd string: hour:minute:second (24 hour clock) e.g. 16:15:00
start_string = [start_time.strftime("%d/%m/%y"), start_time.strftime("%H:%M:%S")]
end_string   = [  end_time.strftime("%d/%m/%y"),   end_time.strftime("%H:%M:%S")]

# START!!!

# Go to https://deltaohm.cloud/
print('Go to https://deltaohm.cloud/')
page.goto('https://deltaohm.cloud/')

# Click input[type="text"]                          (click on the username input)
page.locator('input[type="text"]').click()

# Fill input[type="text"]                           (fill in the username)
page.locator('input[type="text"]').fill('TUNG')

# Press Tab                                         (switch to the password input)
page.locator('input[type="text"]').press('Tab')

# Fill input[type="password"]                       (fill in the password)
page.locator('input[type="password"]').fill('qwert12345')

print('Login')
# Click div[role="button"]:has-text("Login")        (press the login button)
page.locator('div[role="button"]:has-text("Login")').click()
expect(page).to_have_url('https://deltaohm.cloud/#!dashboard')

for device in DEVICES:
    # for each of the DEVICES
    print('DEVICE:', device)

    # Click div[role="button"]:has-text("USERS")   (switch to the USERS page)
    # * this step is to make checking for when the page is done loading easier and 
    #   more accurate when switching back to the DEVICES page since the USERS page 
    #   does not share a lot of the same HTML elements with the devices page unlike 
    #   the HOME page or the DEVICES page itself after the downloading later on at 
    #   the end of this loop
    page.locator('div[role="button"]:has-text("USERS")').click()
    expect(page).to_have_url('https://deltaohm.cloud/#!users')

    # Click div[role="button"]:has-text("DEVICES") (switch to the DEVICES page)
    page.locator('div[role="button"]:has-text("DEVICES")').click()
    expect(page).to_have_url('https://deltaohm.cloud/#!devices')

    # Click on the table cell with the device name  (open the device details on the right)
    page.locator('text=' + device).click()

    # Click span:has-text("View") >> nth=0         (click on the "view" button to open visualization tab)
    page.locator('span:has-text("View")').first.click()

    # Click on the start time - date input and fill it with the date
    fromDay = page.locator('text=From >> [placeholder="__\\/__\\/__"]')
    fromDay.click()
    fromDay.fill(start_string[0])

    # Click on the start time - time input and fill it with the time
    fromTime = page.locator('text=From >> [placeholder="__\\:__\\:__"]')
    fromTime.click()
    fromTime.fill(start_string[1])

    # Click on the end time - date input and fill it with the date
    toDay = page.locator('text=To >> [placeholder="__\\/__\\/__"]')
    toDay.click()
    toDay.fill(end_string[0])

    # Click on the end time - time input and fill it with the time
    toTime = page.locator('text=To >> [placeholder="__\\:__\\:__"]')
    toTime.click()
    toTime.fill(end_string[1])

    # Click div[role="button"]:has-text("")        (click on the update button -> update the data)
    page.locator('div[role="button"]:has-text("")').click()

    # Wait half a second for the time range to take effect
    # * this step is not really necessary i think, just to make sure
    page.wait_for_timeout(500)

    # Click div[role="button"]:has-text("")        (click on the export button)
    page.locator('div[role="button"]:has-text("")').click()

    # Click text=Single File                        (change option to single file download)
    page.locator('text=Single File').click()

    # Click div[role="button"]:has-text("Export")  (click export)
    page.locator('div[role="button"]:has-text("Export")').click()

    # wait 1 second for the exporting
    # * maybe not necessary too?
    page.wait_for_timeout(1000)

    # move the mouse a bit!!!
    # * this is really strange, but the download link will not appear if there is no 
    #   interaction happening on the page. So to make it appears, there must be at least
    #   a mouse event being triggered. The easiest one would be mouse move
    page.mouse.move(400, 400, steps=2)
    page.mouse.move(500, 500, steps=2)
    
    # click on the download button
    with page.expect_download() as download_info:
        page.locator('div[role="button"]:has-text("' + device + '")').click()
    download = download_info.value

    # wait for download to complete
    print('  downloading:', download.path())

    # Save downloaded file somewhere
    download.save_as(ZIP_DIRECTORY + '/data_' + device + '.zip')

    # loop back for another device

# Click text=Bui Do Phuong Tung     (click on the user profile pic for the sign out button to appear)
page.locator('text=Bui Do Phuong Tung').click()

# Click text=Sign out               (sign out)
page.locator('text=Sign out').click()
expect(page).to_have_url('https://deltaohm.cloud/')

# FINISH!!!

browser.close()
playwright.stop()

