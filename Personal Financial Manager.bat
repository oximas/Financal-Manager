@echo off
title PFM Launcher
color 0A

echo.
echo  ======================================
echo   Personal Financial Manager
echo   Starting up...
echo  ======================================
echo.

:: ── Step 1: Start Docker Desktop if not already running ───────────────────
tasklist /FI "IMAGENAME eq Docker Desktop.exe" 2>NUL | find /I "Docker Desktop.exe" >NUL
if errorlevel 1 (
    echo  [1/4] Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo        Waiting for Docker engine to be ready...
    :WAIT_DOCKER
    timeout /t 3 /nobreak >NUL
    docker info >NUL 2>&1
    if errorlevel 1 goto WAIT_DOCKER
    echo        Docker is ready!
) else (
    echo  [1/4] Docker Desktop already running.
    :: Wait for engine to be responsive even if Desktop is open
    :WAIT_DOCKER2
    docker info >NUL 2>&1
    if errorlevel 1 (
        timeout /t 2 /nobreak >NUL
        goto WAIT_DOCKER2
    )
)

echo.

:: ── Step 2: Navigate to project folder ────────────────────────────────────
cd /d "%~dp0"
echo  [2/4] Project folder: %~dp0

echo.

:: ── Step 3: Start containers in background ────────────────────────────────
echo  [3/4] Starting PFM containers...
docker-compose up -d >NUL 2>&1
if errorlevel 1 (
    echo        First run detected - building images (this may take a few minutes^)...
    echo.
    docker-compose up -d --build
    if errorlevel 1 (
        echo.
        echo  ERROR: Failed to start containers.
        echo  Try running: docker-compose up --build
        echo  in this folder to see the error.
        pause
        exit /b 1
    )
)
echo        Containers started!

echo.

:: ── Step 4: Wait for API to be healthy then open browser ──────────────────
echo  [4/4] Waiting for API to be ready...
:WAIT_API
timeout /t 2 /nobreak >NUL
curl -s http://localhost:8000/health >NUL 2>&1
if errorlevel 1 goto WAIT_API
echo        API is ready!

echo.
echo  ======================================
echo   PFM is running!
echo   Opening http://localhost:5173
echo  ======================================
echo.

start "" "http://localhost:5173"

:: ── Keep window open with status ──────────────────────────────────────────
echo  Containers running in background.
echo  Close this window anytime - the app keeps running.
echo.
echo  To stop the app later, run:  docker-compose down
echo  Or double-click: STOP APP.bat
echo.
pause
