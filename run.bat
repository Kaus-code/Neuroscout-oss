@echo off
setlocal
cd /d "%~dp0"
if not exist venv (
    echo Virtual environment not found. Please wait...
    python -m venv venv
    .\venv\Scripts\python -m pip install -r requirements.txt
)
echo Y | .\venv\Scripts\python scout.py %*
pause
