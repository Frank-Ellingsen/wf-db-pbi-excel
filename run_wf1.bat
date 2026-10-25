@echo off
setlocal

set "PYTHON=C:\Users\frank\miniconda3\envs\wf1\python.exe"
set "SCRIPT=C:\Users\frank\Desktop\WF1\src\project_finance\run_all.py"

if not exist "%PYTHON%" (
    echo ERROR: wf1 Python not found:
    echo %PYTHON%
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo ERROR: run_all.py not found:
    echo %SCRIPT%
    pause
    exit /b 1
)

"%PYTHON%" "%SCRIPT%"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo WF1 completed successfully.
) else (
    echo WF1 failed. Exit code: %RC%
)

echo.
pause
exit /b %RC%
