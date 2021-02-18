# gimme-omni
Grabs existing Omni-Channel cases and shows what your new staleness and queue position would be if you were to accept one

## What it does
Retrieves the list of currently available Omni-Channel cases, computes what your new staleness and queue position would be if you accepted one of those cases (based on your current staleness and the percent reduction associated with each case), and finally prints the results to console in a nicely-formatted table.

<img src="https://github.com/chulock56/gimme-omni/blob/main/sampleImg.png"/>

## How it works
Uses the standard Python library, including the following modules:
- json
- time
- calendar

Also uses the following community modules:
- requests
- requests-kerberos
- tabulate

Staleness, position, and Omni case data is retrieved via the TSOps API.

## How to get it working on your computer
1. Install Python3 (https://www.python.org/downloads/)
2. Install the following modules to your Python environment (all available from PyPi. See links for installation instructions):
    * requests (https://pypi.org/project/requests/)
    * requests-kerberos (https://pypi.org/project/requests-kerberos/)
    * tabulate (https://pypi.org/project/tabulate/)
3. Download the code from this Repo and extract it to the directory of your choice. (I use C:\Users\NAME\PythonScripts\)
4. Add this directory to PATH (instructions: https://docs.alfresco.com/4.2/tasks/fot-addpath.html)
5. Modify LINE 5 of the .bat file to use:
    * The directory of your Python environment (i.e. install directory; location of python.exe)
    * The directory where you extracted the tsopsStalenessCalc.py script
6. Modify LINE 19 of the tsopsStalenessCalc.py file to use the URI of your profile (e.g. achulock is mine). This should follow the format of your email address.
7. If needed, you will have to modify the tsopsStalenessCalc.py file to include any languages other than English in the logic:
    * By default, the script is written to only include English Omni-channel cases. You need to modify LINE 70 if you want to include other languages.
    * By default, the script only calculates your new position in the English queue. You need to modify LINE 86 if you want to calculate new position in a queue other than English. Currently, you cannot compute new position for multiple queues.
9. Add the TSOps certificate chain to your Python trusted certificates list. Details are in the script file itself, starting at LINE 4.
10. If you added the directory to PATH, you should be able to run the .bat file from the Windows Run dialog (Windows Key + R) without specifying a path to the directory.
