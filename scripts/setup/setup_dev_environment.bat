@echo off
REM Development Environment Setup Script
REM Ensures proper configuration for folder-datetime-fix development

echo ==================================================
echo DEVELOPMENT ENVIRONMENT SETUP
echo Folder DateTime Fix - UNCtools Integration
echo ==================================================
echo.

REM Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.9+ and add to PATH
    exit /b 1
)

echo Step 1: Installing/Updating dependencies...
echo.

REM Install UNCtools from PyPI (optional -- enables enhanced UNC path support)
echo Installing UNCtools from PyPI...
pip install --upgrade unctools >nul 2>&1
if errorlevel 1 (
    echo Warning: Could not install unctools from PyPI
    echo UNC enhancement is optional; basic path handling will be used.
    echo See https://pypi.org/project/unctools/
)

REM Install other requirements
if exist requirements.txt (
    echo Installing requirements.txt...
    pip install -r requirements.txt >nul 2>&1
)

echo.
echo Step 2: Setting environment variables...

REM Confirm UNCtools is importable (optional enhancement)
python -c "import unctools" >nul 2>&1
if errorlevel 1 (
    echo UNCtools not installed -- UNC enhancement disabled.
    echo To enable: pip install unctools
)

echo.
echo Step 3: Validating environment...
echo.

REM Run validation script
python scripts\validate_dev_environment.py
if errorlevel 1 (
    echo.
    echo ==================================================
    echo SETUP INCOMPLETE
    echo ==================================================
    echo Some validation checks failed.
    echo Please review the output above and follow the recommendations.
    echo.
    echo For detailed diagnosis, run:
    echo   python scripts\diagnose_unctools_env.py
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo SETUP COMPLETE
echo ==================================================
echo Development environment is properly configured!
echo.
echo You can now use:
echo   fdtfix.py [arguments]
echo   python -m folder_datetime_fix [arguments]
echo.
echo For UNC path support:
echo   fdtfix.py --unc-path "\\server\share" [options]
echo.
pause