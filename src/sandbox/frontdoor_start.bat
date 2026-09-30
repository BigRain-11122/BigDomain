@echo off
rem XL-16 one-click relauncher for the BigDomain sandbox front door.
rem Starts a detached local server on http://127.0.0.1:8093/
cd /d %~dp0
start "BigDomain-frontdoor" /min python frontdoor.py
