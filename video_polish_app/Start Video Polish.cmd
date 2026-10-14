@echo off
cd /d "%~dp0.."
".venv_phase7\Scripts\python.exe" "video_polish_app\app.py"
if errorlevel 1 pause
