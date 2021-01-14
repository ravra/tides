# Script to fetch predicted tides for Santa Cruz/Monterey Bay. Specifically, it screens for very low tides
# (below 0) during certain hours of the day since these are the best times to bike on the beach

# Installation
# Requires BeautifulSoup4, requests-html, and my sendMeMail
# Important: requests-html installs the Chromium browser in the home directory. However, on RPI it installed the x86 version
# and caused an "Exec format" error. To fix this:
#
# 1) Delete all files from that directory (i.e. rm /home/pi/.local/share/pyppeteer/local-chromium/588429/chrome-linux/*)
# 2) Perform a normal installation of Chromium (i.e. sudo apt-get install chromium-browser)
# 3) Create a symbolic link to that version (i.e. ln -s /usr/bin/chromium-browser /home/pi/.local/share/pyppeteer/local-chromium/588429/chrome)

# https://github.com/ravra/tides

import sys, argparse, datetime, time, sendMeMail

from requests_html import HTMLSession # This is required due to javascript usage in the target NOAA website

from bs4 import BeautifulSoup

# Command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--early", help="Earliest time each day", default="10:00 AM")
parser.add_argument("--late", help="Latest time each day", default="4:00 PM")
parser.add_argument("--month", help="Month to check for tides. Default is next 31 days. Using 'next' will fetch next month's data", default="current")
parser.add_argument("--lowTideLevel", help="Low tide maximum level", default=0)
parser.add_argument("--test", help="Use test structures and don't fetch", action="store_true")
parser.add_argument("--test12", help="Test December change", action="store_true")
parser.add_argument("--print", help="Print out message", action="store_true")

args = parser.parse_args()

testRow = ['2021/01/27', 'Wed', '4:15 PM', '-0.82', 'L'] # Used in testing

session = HTMLSession()

session.headers.update({'User-Agent': 'Custom user agent'})

firstDay   = datetime.datetime.today()   # By default, the first day to check is today
allDays    = datetime.timedelta(days=31) # A delta time object of 31 days

# Test for December since it is a special case
if args.test12:
    firstDay = datetime.datetime.strptime(firstDay.strftime('%Y') + '/12/01', '%Y/%m/%d') # Just to test for the Dec-to-Jan transition

# The default is to fetch the tides for the next 31 days but by specifying "--month next" it can get the tides for next month
if args.month == "next":
    if firstDay.strftime('%m') != "12":  # For first 11 months - i.e. not December
        # Increment month to next month. Use int/str to avoid worrying about number of days to add
        # firstDay will be the first day of next month
        firstDay = datetime.datetime.strptime(firstDay.strftime('%Y') + '/' + str(int(firstDay.strftime('%m')) +1) + '/' + '01', '%Y/%m/%d')
    else:  # December is a special case
        # Move date object to January simply by adding 31 days (Dec & Jan both have 31 so no risk of jumping over a month)
        firstDay = firstDay+allDays
        firstDay = datetime.datetime.strptime(firstDay.strftime('%Y') + '/' + firstDay.strftime('%m') + '/' + '01', '%Y/%m/%d')

inOneMonth = firstDay+allDays              # 31 days beyond firstDay since that is what the website can handle
dateStart  = firstDay.strftime('%Y%m%d')   # dateStart, dateEnd are used in the URL
dateEnd    = inOneMonth.strftime('%Y%m%d')


message = "Note: Checking dates from {dateStart} to {dateEnd}\n".format(dateStart=dateStart, dateEnd=dateEnd)

# Form the URL to fetch from
url = "https://tidesandcurrents.noaa.gov/noaatidepredictions.html?id=9413616&units=standard&bdate="+dateStart+"&edate="+dateEnd+"&timezone=LST/LDT&clock=12hour&datum=MLLW"


if not args.test:
    response = session.get(url)

    # This call executes the javascript in the page. The sleep seems to be necessary to provide sufficient time.
    response.html.render(timeout=20, sleep=15)  

    soup = BeautifulSoup(response.html.raw_html, "html.parser")

    # This locates the table of tides in the returned webpage
    tideTable = soup.find('table', id="data_listing_table")

    tableRows = tideTable.find_all('tr')  # Start parsing the table

    index = 0
    lowTides = []

    for tr in tableRows:
        td = tr.find_all('td')
        row = [i.text for i in td]
        if len(row) > 0:
            row[3] = float(row[3])           # Convert tide number string to float for comparison or sorting...
            if row[4] == "L":                # Only looking for low tides
                if row[3] <= args.lowTideLevel:   # Only print tides lower than the lowTideLevel (default: 0)
                    lowTides.append(row)
                    # print(lowTides[index])
                    index = index + 1

else:             # Used for testing
    lowTides = [
        ['2021/01/01', 'Fri', '04:54 AM', '2.74', 'L'],
        ['2021/01/01', 'Fri', '6:30 PM', '-0.74', 'L'],
        ['2021/01/02', 'Sat', '05:46 AM', '2.72', 'L'],
        ['2021/01/02', 'Sat', '7:09 PM', '-0.56', 'L'],
        ['2021/01/03', 'Sun', '06:49 AM', '2.65', 'L'],
        ['2021/01/03', 'Sun', '7:50 PM', '-0.27', 'L'],
        ['2021/01/04', 'Mon', '08:05 AM', '2.47', 'L'],
        ['2021/01/04', 'Mon', '8:33 PM', '0.14', 'L'],
        ['2021/01/05', 'Tue', '09:31 AM', '2.11', 'L'],
        ['2021/01/05', 'Tue', '9:18 PM', '0.62', 'L'],
        ['2021/01/06', 'Wed', '10:56 AM', '1.54', 'L'],
        ['2021/01/06', 'Wed', '10:06 PM', '1.12', 'L']
    ]


# lowTides.sort(key=lambda x:x[3])  # Use this to sort by tide height but chronological seems more useful

i = 0

while i < len(lowTides):  # Check if low tide is within the interesting hours
    tideTime  = datetime.datetime.strptime(lowTides[i][0] + ' ' + lowTides[i][2], "%Y/%m/%d %I:%M %p")
    timeEarly = datetime.datetime.strptime(lowTides[i][0] + ' ' + args.early,     "%Y/%m/%d %I:%M %p")
    timeLate  = datetime.datetime.strptime(lowTides[i][0] + ' ' + args.late,      "%Y/%m/%d %I:%M %p")
    if ((tideTime >= timeEarly) and (tideTime <= timeLate)):
        #print("Time to ride! ", tideTime.strftime('%Y/%m/%d %H:%M %a'), " with low tide of ", lowTides[i][3])
        message = "{msg}Time to ride! {tideTimeStr} with low tide of {tideLevelStr}\n".format(msg = message, tideTimeStr = tideTime.strftime('%Y/%m/%d %H:%M %a'),  tideLevelStr = lowTides[i][3])
    i = i + 1

sendMeMail.sendMeMail("Time to ride!", message)
if args.print:
    print(message)
sys.exit()
