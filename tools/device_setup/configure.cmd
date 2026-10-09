@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe device.py configure %*
pause
