@echo off
title PFM - Stopping
color 0C

echo.
echo  ======================================
echo   Stopping PFM...
echo  ======================================
echo.

cd /d "%~dp0"

docker-compose down
echo.
echo  All containers stopped.
echo  Your data is safe in the Docker volume.
echo.
pause
