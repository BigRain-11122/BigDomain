@echo off
rem XL-17 one-click launcher for the whole BigDomain sandbox (nine faces).
rem Starts every face, waits for the measured hub URL, opens the browser there.
rem Closing this window tears the sandbox down (job object kill-on-close).
cd /d "%~dp0"
python "src\sandbox\open_sandbox.py"
if errorlevel 1 pause
