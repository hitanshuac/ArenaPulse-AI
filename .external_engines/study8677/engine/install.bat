@echo off
REM Antigravity repository knowledge engine installer for Windows.

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%.."

echo.
echo Antigravity Repository Knowledge Engine - Installer
echo ===================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    popd
    pause
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Error: Python !PYTHON_VERSION! detected. Python 3.10 or higher is required.
    popd
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python !PYTHON_VERSION! detected

git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed.
    echo Please install Git from https://git-scm.com/downloads
    popd
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
echo Git !GIT_VERSION! detected
echo.

echo Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        popd
        pause
        exit /b 1
    )
    echo Virtual environment created
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    popd
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo Warning: pip upgrade had issues, continuing...
)

echo Installing Antigravity CLI and engine...
python -m pip install -e ./cli -e ./engine[dev] --quiet
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    popd
    pause
    exit /b 1
)
echo Dependencies installed

echo Setting up local configuration...
if not exist ".env" (
    (
        echo # Antigravity local configuration
        echo # This file is for trusted local development. Keep real credentials out of git.
        echo.
        echo # OpenAI-compatible endpoint
        echo OPENAI_BASE_URL=https://your-endpoint/v1
        echo OPENAI_API_KEY=your-key
        echo OPENAI_MODEL=your-model
        echo.
        echo # Retrieval graph mode: off, compact, or full.
        echo AG_RETRIEVAL_MODE=compact
    ) > .env
    echo Created .env file
) else (
    echo .env file already exists. Skipping creation.
)

if exist ".gitignore" (
    findstr /x /c:".env" .gitignore >nul 2>&1
    if errorlevel 1 (
        echo.>> .gitignore
        echo .env>> .gitignore
    )
)

if not exist "artifacts\" mkdir artifacts
if not exist ".antigravity\" mkdir .antigravity

echo.
echo ===================================================
echo Installation complete.
echo.
echo Next steps:
echo 1. Run /ag-setup in your agent host, or configure OPENAI_* in .env.
echo 2. The virtual environment is already activated.
echo 3. Build repository knowledge:
echo    ag-refresh --workspace .
echo 4. Ask a repository question:
echo    ag-ask "How does this project work?" --workspace .
echo.
echo Documentation: docs/en/QUICK_START.md
echo ===================================================
echo.
popd
pause
