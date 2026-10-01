@echo off
REM Take a clean clone to a running application in one command (Windows).
REM The POSIX equivalent is deploy.sh; this file exists because the clean-checkout
REM verification (WBS 5.3, Definition of Done criterion 5) is run by team members
REM on Windows, and a step that cannot be reproduced is not evidence.
REM
REM Usage:  deploy.bat

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo ==^> Checking the Python prerequisite
where py >nul 2>&1
if %errorlevel%==0 (
    set "BOOT=py -3"
) else (
    where python >nul 2>&1
    if !errorlevel! neq 0 (
        echo ERROR: Python 3.11 or newer is required but was not found on PATH.
        exit /b 1
    )
    set "BOOT=python"
)

%BOOT% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required.
    %BOOT% --version
    exit /b 1
)
for /f "delims=" %%v in ('%BOOT% --version 2^>^&1') do echo ==^> Using %%v

if not exist "%VENV_DIR%" (
    echo ==^> Creating virtual environment in %VENV_DIR%
    %BOOT% -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
) else (
    echo ==^> Reusing the existing virtual environment in %VENV_DIR%
)

if not exist "%VENV_PY%" (
    echo ERROR: Could not find %VENV_PY%.
    exit /b 1
)

echo ==^> Installing development and test tooling ^(no runtime dependencies^)
"%VENV_PY%" -m pip install --quiet --upgrade pip
if errorlevel 1 exit /b 1
"%VENV_PY%" -m pip install --quiet -r requirements.txt
if errorlevel 1 exit /b 1

echo ==^> Installing the package in editable mode
"%VENV_PY%" -m pip install --quiet -e .
if errorlevel 1 exit /b 1

if not exist "config.env" (
    echo ==^> Creating config.env from config.env.template
    copy /y "config.env.template" "config.env" >nul
) else (
    echo ==^> Keeping the existing config.env ^(never overwritten^)
)

echo ==^> Smoke check: python -m warrigal --version
"%VENV_PY%" -m warrigal --version
if errorlevel 1 exit /b 1

echo ==^> Running the test suite
"%VENV_PY%" -m pytest -q
if errorlevel 1 exit /b 1

echo.
echo ==^> Done. Activate the environment with:  %VENV_DIR%\Scripts\activate
endlocal
