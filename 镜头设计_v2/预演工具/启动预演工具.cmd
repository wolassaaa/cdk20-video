@echo off
rem Serves this folder on localhost (the browser only allows the camera on http://localhost) and opens the page.
cd /d "%~dp0"
start "" http://localhost:8765/
py -m http.server 8765
