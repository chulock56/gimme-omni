# This script gets data from the TSOps API and prints your hypothetical new staleness if you accepted and Omni case
#
# NOTES:
# tsops certificate is required to make requests. to import, open tsops in browser,
# export the chain of certificates from URL (click the padlock icon next the the URL > select certificate > 
# Details tab > Copy to file... ) and save as Base64 encoded .cer files. 
# You will need to export the entire chain of certificates this way.
# open the exported certs in Notepad++ and copy/paste the information to the bottom of your cacert.pem file. 
# This file is located at:
# ...\\Python<Build#>\\lib\\site-packages\\certifi\\cacert.pem
#
# You must adjust the URI in the "Request to get staleness value" section to your own username (same as your OSI email)

import requests
from requests_kerberos import HTTPKerberosAuth
import json
import time
import calendar
from tabulate import tabulate

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Request to get staleness value ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
resStale = requests.get('https://tsops-api-phl.dev.osisoft.int/api/agents/achulock', auth=HTTPKerberosAuth())
resStale.raise_for_status()  # check that above request  was successful, raise exception if not

resStaleJson = resStale.json()  # convert response to json format
resStaleJsonFormatted = json.dumps(resStaleJson, indent=2)  # format JSON

lastContactTime = resStaleJson['adjustedLastContactEndTime']

# Convert the adjustedLastContactEndTime to your staleness, in seconds
lastContactTime_parsed = time.strptime(lastContactTime, "%Y-%m-%dT%H:%M:%S.%fZ")  # parse last contact time into tuple
lastContact_unixTime = calendar.timegm(lastContactTime_parsed)  # convert time tuple to unix epoch time (UTC)
staleness = round((time.time() - lastContact_unixTime))  # calculate staleness in seconds

# Format staleness in seconds to d.HH:MM:SS
staleDays = staleness // (24 * 3600)
remainder = staleness % (24 * 3600)
staleHours = remainder // 3600
remainder = remainder % 3600
staleMinutes = remainder // 60
staleSeconds = remainder % 60

staleness_formatted = '%d.%02d:%02d:%02d' % (staleDays, staleHours, staleMinutes, staleSeconds)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Request to get current omni cases ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
resOmni = requests.get('https://tsops-api-phl.dev.osisoft.int/api/cases/current', auth=HTTPKerberosAuth())
resOmni.raise_for_status()  # check that above request  was successful, raise exception if not

resOmniJson = resOmni.json()  # convert response to json format
resOmniJsonFormatted = json.dumps(resOmniJson, indent=2)  # format JSON

# Filter out any non-Omni, frontline, English cases
omniCases = []
for case in resOmniJson:
    if case['category'] == 1 and case['origin'] != "Back Line Request" and case['language'] == "English":
        # category 1 means omni-channel (0 = reassignment)
        omniCases.append([case['subject'], case['timestamp'], 0])  # 0 is a placeholder for the % staleness reduction
        # format of list of lists: [['<CaseName>', '<CaseTimestamp>', <StalenessReduction>], ...]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Manipulate the retrieved data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Convert the creation time of the omni cases to duration in queue, and calculate the corresponding staleness reduction
for i, group in enumerate(omniCases):
    timestamp_parsed = time.strptime(group[1], "%Y-%m-%dT%H:%M:%S.%fZ")  # parse the start time into tuple
    unix_time = calendar.timegm(timestamp_parsed)  # convert time tuple to unix epoch time (UTC)
    timeDifHours = (time.time() - unix_time) / 3600  # difference between current UTC epoch and case UTC epoch in hours

    # apply formula to find percent staleness reduction
    reduction = min(round(25 + (75 * timeDifHours / 3.5)), 100)

    omniCases[i][2] = reduction  # assign % staleness reduction to the inner list


# Modify list of lists: replace case creation timestamp with new staleness value
for i, group in enumerate(omniCases):
    newStaleness = staleness * 0.01 * (100 - group[2])

    # convert new staleness in seconds to days, hours, mins, secs
    newStaleDays = newStaleness // (24 * 3600)
    remainder = newStaleness % (24 * 3600)
    newStaleHours = remainder // 3600
    remainder = remainder % 3600
    newStaleMinutes = remainder // 60
    newStaleSeconds = remainder % 60

    newStaleness_formatted = '%d.%02d:%02d:%02d' % (newStaleDays, newStaleHours, newStaleMinutes, newStaleSeconds)

    omniCases[i][1] = newStaleness_formatted  # assign the formatted new staleness to the inner list


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Print the final results table to console ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
print('\n#-#-#-#-#-#-#-#\nCurrent Staleness: ' + staleness_formatted + '\n')  # print current staleness

# print hypothetical stalenesses in a table
try:
    print(tabulate(omniCases, headers=["Case", "New Staleness", "Reduction (%)"], tablefmt="grid",
                   colalign=("right", "left", "left")))
except IndexError as err:
    print('No Omni cases currently in queue or some other IndexError. Exception:\n{0}'.format(err))

