@echo off
echo Testing UNCtools detection in CMD environment
echo.

echo Python version:
python --version
echo.

echo Direct UNCtools test:
python -c "try: import unctools; print('SUCCESS: UNCtools available'); except Exception as e: print('FAILED:', e)"
echo.

echo UNC handler test:
python -c "from folder_datetime_fix.unc_handler import UNCTOOLS_AVAILABLE; print('UNC handler UNCTOOLS_AVAILABLE:', UNCTOOLS_AVAILABLE)"
echo.

echo CLI verbose test (should show UNCtools status):
python -m folder_datetime_fix --version
echo.

pause
