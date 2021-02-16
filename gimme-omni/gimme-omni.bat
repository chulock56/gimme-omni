@echo off
:start
cls

@C:\Python38-32\python.exe C:\Users\achulock\PythonScripts\tsopsStalenessCalc.py

set choice=
set /p choice="Run again? Enter 'y' or 'n' (Yes/No): "
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto start

:: Change the path above to match your python3 environment and the location of the tsopsStalenessCalc.py script
:: The tsopsStalenessCalc.py script directory should be added to PATH if you
:: 	wish to have the option to run the script from the Windows "Run" dialog (WindowsKey + R)
:: You can create a desktop shortcut pointing to this .bat file to easily run the python script as well.
