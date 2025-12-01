@echo off
cd /d "%~dp0"
echo Initializing WSL...
wsl echo "WSL Initialized"
.\Game\venv\Scripts\python.exe Game\main.py
pause
