@echo off
echo Installing packages for 32-bit Python...
echo.

C:\Python312-32\python.exe --version
if errorlevel 1 (
    echo ERROR: 32-bit Python not found at C:\Python312-32\python.exe
    echo Please install Python 3.12 32-bit to C:\Python312-32
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
C:\Python312-32\python.exe -m pip install --upgrade pip

echo.
echo Installing PyQt5...
C:\Python312-32\python.exe -m pip install pyqt5==5.15.10

echo.
echo Installing pywin32...
C:\Python312-32\python.exe -m pip install pywin32

echo.
echo Installation complete!
echo.
echo You can now run the GUI application and use Kiwoom API features.
pause
