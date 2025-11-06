@echo off
echo ========================================
echo 키움 백테스팅 시스템 32비트 환경 설정
echo ========================================
echo.

REM 32비트 Python 경로 찾기
set PYTHON32=
if exist "C:\Users\AND\AppData\Local\Programs\Python\Python311-32\python.exe" (
    set PYTHON32=C:\Users\AND\AppData\Local\Programs\Python\Python311-32\python.exe
) else if exist "C:\Users\AND\AppData\Local\Programs\Python\Python312-32\python.exe" (
    set PYTHON32=C:\Users\AND\AppData\Local\Programs\Python\Python312-32\python.exe
) else (
    echo [오류] 32비트 Python을 찾을 수 없습니다.
    echo.
    echo 다음 경로 중 하나에 32비트 Python을 설치해주세요:
    echo - C:\Users\AND\AppData\Local\Programs\Python\Python311-32
    echo - C:\Users\AND\AppData\Local\Programs\Python\Python312-32
    echo.
    echo Python 32비트 다운로드:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [확인] 32비트 Python 찾음: %PYTHON32%
echo.

REM Python 비트 확인
%PYTHON32% -c "import platform; bits = platform.architecture()[0]; print(f'Python: {bits}'); exit(0 if bits == '32bit' else 1)"
if errorlevel 1 (
    echo [오류] 64비트 Python입니다. 32비트가 필요합니다.
    pause
    exit /b 1
)

REM 기존 venv 삭제
if exist venv (
    echo [삭제] 기존 가상환경 제거 중...
    rmdir /s /q venv
)

REM 새 venv 생성
echo [생성] 32비트 가상환경 생성 중...
%PYTHON32% -m venv venv
if errorlevel 1 (
    echo [오류] 가상환경 생성 실패
    pause
    exit /b 1
)

REM pip 업그레이드
echo [업그레이드] pip 업그레이드 중...
.\venv\Scripts\python.exe -m pip install --upgrade pip

REM 의존성 설치
echo [설치] 의존성 설치 중...
.\venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [오류] 의존성 설치 실패
    pause
    exit /b 1
)

echo.
echo ========================================
echo 설치 완료!
echo ========================================
echo.
echo 이제 run_gui.bat를 실행하여 프로그램을 시작할 수 있습니다.
echo.
pause
