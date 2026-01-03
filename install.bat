@echo off
REM Telegram Channel Monitor - Windows Installation Script
REM Downloads latest code from GitHub and installs to %USERPROFILE%\.tgmonitor
REM Compatible with Windows 7 and Python 3.8.9+

setlocal enabledelayedexpansion

echo ========================================
echo Telegram Channel Monitor - Installer
echo ========================================
echo.

REM GitHub repository information
set "REPO_URL=https://github.com/8nevil8/telegram-channel-monitor"
set "ZIP_URL=https://github.com/8nevil8/telegram-channel-monitor/archive/refs/heads/master.zip"
set "TEMP_DIR=%TEMP%\tgmonitor-install"
set "INSTALL_DIR=%USERPROFILE%\.tgmonitor"

echo Repository: %REPO_URL%
echo Installation directory: %INSTALL_DIR%
echo.

REM Step 1: Check Python version
echo [1/12] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Parse major and minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

REM Check if version is >= 3.8
if %PYTHON_MAJOR% LSS 3 (
    echo ERROR: Python 3.8 or higher is required. Found: %PYTHON_VERSION%
    pause
    exit /b 1
)
if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 8 (
    echo ERROR: Python 3.8 or higher is required. Found: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo Python version OK
echo.

REM Step 2: Clean up any previous temporary downloads
echo [2/12] Preparing temporary directory...
if exist "%TEMP_DIR%" (
    echo Cleaning up previous download...
    rmdir /s /q "%TEMP_DIR%"
)
mkdir "%TEMP_DIR%"
echo Temporary directory ready
echo.

REM Step 3: Download latest code from GitHub
echo [3/12] Downloading latest code from GitHub...
echo This may take a moment...
powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%TEMP_DIR%\repo.zip'" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to download code from GitHub
    echo Please check your internet connection and try again
    echo Or download manually from: %REPO_URL%
    pause
    exit /b 1
)
echo Download complete
echo.

REM Step 4: Extract downloaded ZIP
echo [4/12] Extracting files...
powershell -Command "Expand-Archive -Path '%TEMP_DIR%\repo.zip' -DestinationPath '%TEMP_DIR%' -Force" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to extract downloaded files
    pause
    exit /b 1
)
echo Files extracted
echo.

REM Find the extracted directory (will be telegram-channel-monitor-master or similar)
for /d %%i in ("%TEMP_DIR%\telegram-channel-monitor-*") do set "EXTRACTED_DIR=%%i"
if not exist "%EXTRACTED_DIR%" (
    echo ERROR: Could not find extracted directory
    pause
    exit /b 1
)

echo Working from: %EXTRACTED_DIR%
echo.

REM Step 5: Create installation directory structure
echo [5/12] Creating directory structure...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\app" mkdir "%INSTALL_DIR%\app"
if not exist "%INSTALL_DIR%\app\src" mkdir "%INSTALL_DIR%\app\src"
echo Directory structure created
echo.

REM Step 6: Copy source files
echo [6/12] Copying source files...
copy /Y "%EXTRACTED_DIR%\src\__init__.py" "%INSTALL_DIR%\app\src\" >nul
copy /Y "%EXTRACTED_DIR%\src\main.py" "%INSTALL_DIR%\app\src\" >nul
copy /Y "%EXTRACTED_DIR%\src\monitor.py" "%INSTALL_DIR%\app\src\" >nul
copy /Y "%EXTRACTED_DIR%\src\matcher.py" "%INSTALL_DIR%\app\src\" >nul
copy /Y "%EXTRACTED_DIR%\src\notifier.py" "%INSTALL_DIR%\app\src\" >nul
echo Source files copied
echo.

REM Step 7: Copy requirements.txt
echo [7/12] Copying requirements.txt...
copy /Y "%EXTRACTED_DIR%\requirements.txt" "%INSTALL_DIR%\app\" >nul
echo Requirements.txt copied
echo.

REM Step 8: Copy config.example.yaml (only if not exists)
echo [8/12] Setting up configuration...
if not exist "%INSTALL_DIR%\config.yaml" (
    copy "%EXTRACTED_DIR%\config.example.yaml" "%INSTALL_DIR%\config.yaml" >nul
    echo Created config.yaml from template
) else (
    echo Existing config.yaml preserved
)
echo.

REM Step 9: Copy .env.example (only if not exists)
echo [9/12] Setting up environment file...
if not exist "%INSTALL_DIR%\.env" (
    copy "%EXTRACTED_DIR%\.env.example" "%INSTALL_DIR%\.env" >nul
    echo Created .env from template
) else (
    echo Existing .env preserved
)
echo.

REM Step 10: Create virtual environment
echo [10/12] Creating virtual environment...
if exist "%INSTALL_DIR%\venv" (
    echo Removing old virtual environment...
    rmdir /s /q "%INSTALL_DIR%\venv"
)
python -m venv "%INSTALL_DIR%\venv"
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Step 11: Install dependencies
echo [11/12] Installing dependencies...
echo This may take a few minutes...
call "%INSTALL_DIR%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install -r "%INSTALL_DIR%\app\requirements.txt" --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Step 12: Generate tgmonitor.bat run script
echo [12/12] Creating run script...
(
echo @echo off
echo REM Telegram Channel Monitor - Run Script
echo REM Generated by install.bat
echo.
echo REM Change to installation directory
echo cd /d "%%~dp0"
echo.
echo REM Activate virtual environment
echo call venv\Scripts\activate.bat
echo if errorlevel 1 ^(
echo     echo ERROR: Failed to activate virtual environment
echo     echo Please run install.bat again to reinstall
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Run the monitor
echo python -m app.src.main %%*
echo.
echo REM Handle errors
echo if errorlevel 1 ^(
echo     echo.
echo     echo Monitor stopped with errors
echo     pause
echo ^)
) > "%INSTALL_DIR%\tgmonitor.bat"
echo Run script created
echo.

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Telegram Monitor.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\tgmonitor.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Telegram Channel Monitor'; $Shortcut.Save()" 2>nul

if errorlevel 1 (
    echo WARNING: Could not create desktop shortcut
    echo You can manually create a shortcut to: %INSTALL_DIR%\tgmonitor.bat
) else (
    echo Desktop shortcut created
)
echo.

REM Clean up temporary files
echo Cleaning up temporary files...
rmdir /s /q "%TEMP_DIR%" 2>nul
echo.

REM Installation complete
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Installation directory: %INSTALL_DIR%
echo Repository: %REPO_URL%
echo.
echo NEXT STEPS:
echo.
echo 1. Edit configuration file:
echo    notepad "%INSTALL_DIR%\config.yaml"
echo    - Configure channels to monitor
echo    - Set up products and keywords
echo.
echo 2. Edit environment file:
echo    notepad "%INSTALL_DIR%\.env"
echo    - Add your Telegram API credentials from https://my.telegram.org/apps
echo    - Set API_ID, API_HASH, and PHONE_NUMBER
echo.
echo 3. Run the monitor:
echo    - Double-click "Telegram Monitor" shortcut on your Desktop
echo    - OR run: %INSTALL_DIR%\tgmonitor.bat
echo.
echo 4. On first run:
echo    - Enter the authentication code sent to your Telegram app
echo    - Session will be saved for future runs
echo.
echo To update:
echo    Just run this install.bat script again (preserves your config and session)
echo.
echo To uninstall: Delete %INSTALL_DIR%
echo.
echo Press any key to exit...
pause >nul
