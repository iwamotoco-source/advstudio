@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
 py -3 Start_Studio.py
) else (
 python Start_Studio.py
)
pause
