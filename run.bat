@echo off
REM Activate virtual environment and run the monitor (Windows)

call venv\Scripts\activate.bat
python -m src.main %*
