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


# ~~~~~~~~~~~~~~~~~~~~~~~ Function to convert from time string to Unix Time  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def convert_to_staleness(timestring: str) -> int:
    timestringParsed = time.strptime(timestring, "%Y-%m-%dT%H:%M:%S.%fZ")  # parse last contact time into tuple
    unixTime = calendar.timegm(timestringParsed)  # convert time tuple to unix epoch time (UTC)
    timeDif = round((time.time() - unixTime))  # calculate time difference in seconds

    return timeDif


# ~~~~~~~~~~~~~~~~~~~ Function to convert from Unix Time to formatted time string ~~~~~~~~~~~~~~~~~~~~~~~~~~
def format_staleness(staleness_unix: int) -> str:
    # Format staleness in seconds to d.HH:MM:SS
    staleDays = staleness_unix // (24 * 3600)
    remainder = staleness_unix % (24 * 3600)
    staleHours = remainder // 3600
    remainder = remainder % 3600
    staleMinutes = remainder // 60
    staleSeconds = remainder % 60

    return '%d.%02d:%02d:%02d' % (staleDays, staleHours, staleMinutes, staleSeconds)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Request to get staleness value ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
resStale = requests.get('https://tsops-api-phl.dev.osisoft.int/api/agents/achulock', auth=HTTPKerberosAuth())
resStale.raise_for_status()  # check that above request  was successful, raise exception if not

resStaleJson = resStale.json()  # convert response to json format
resStaleJsonFormatted = json.dumps(resStaleJson, indent=2)  # format JSON

lastContactTime = resStaleJson['adjustedLastContactEndTime']

# Convert the adjustedLastContactEndTime to your staleness, in seconds
staleness = convert_to_staleness(lastContactTime)

# Format staleness in seconds to d.HH:MM:SS
staleness_formatted = format_staleness(staleness)


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
        omniCases.append([case['subject'], case['timestamp'], 0, 0])  # 0s are placeholders
        # format of list of lists: [['<CaseName>', '<CaseTimestamp>', <StalenessReduction>, <NewQueuePos>], ...]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Request to get TSOps available agents ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
resQueue = requests.get('https://tsops-api-phl.dev.osisoft.int/api/agents/simple', auth=HTTPKerberosAuth())
resQueue.raise_for_status()  # check that above request  was successful, raise exception if not

resQueueJson = resQueue.json()  # convert response to json format
resQueueJsonFormatted = json.dumps(resQueueJson, indent=2)  # format JSON

queue = []
for n in resQueueJson:
    # list should only include available agents with English skill
    if n['state'] == "Available" and 'fl_english_ib' in n['skills']:
        agentStaleness = convert_to_staleness(n['adjustedLastContactEndTime'])
        queue.append(agentStaleness)

queue.sort(reverse=True)  # sort list of available agents from greatest to least staleness


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Manipulate the retrieved data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Convert the creation time of the omni cases to duration in queue, and calculate the corresponding staleness reduction
for i, group in enumerate(omniCases):
    timeDifHours = convert_to_staleness(group[1]) / 3600  # diff between current UTC secs and case UTC secs in hours

    # apply formula to find percent staleness reduction
    reduction = min(round(25 + (75 * timeDifHours / 3.5)), 100)

    omniCases[i][2] = reduction  # assign % staleness reduction to the inner list

# Modify list of lists: replace case creation timestamp with new staleness value; and add new position in queue
for i, group in enumerate(omniCases):
    newStaleness = staleness * 0.01 * (100 - group[2])

    # search through the queue and find what your new position would be for each case
    pos = 0
    while newStaleness < queue[pos]:
        pos += 1
        continue
    else:
        if pos == 0:
            omniCases[i][3] = 1
        else:
            omniCases[i][3] = pos

    newStaleness_formatted = format_staleness(newStaleness)  # convert new staleness in unix to days, hours, mins, secs

    omniCases[i][1] = newStaleness_formatted  # assign the formatted new staleness to the inner list


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Print the final results table to console ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
print('\nCurrent Staleness: ' + staleness_formatted + '\n')  # print current staleness

# print hypothetical stalenesses in a table
try:
    print(tabulate(omniCases, headers=["Case", "New Staleness", "Reduction (%)", "New Position"], tablefmt="grid",
                   colalign=("right", "left", "left", "left")))
except IndexError as err:
    print('No Omni cases currently in queue or some other IndexError. Exception:\n{0}'.format(err))
