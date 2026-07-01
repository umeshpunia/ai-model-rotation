@echo off
title Claude Code via AI Gateway
echo ======================================================
echo Launching Claude Code via AI Gateway Pro...
echo ======================================================

:: Parse configuration from .env
set PORT=8080
set HOST=127.0.0.1
set PREFIX=/v1

if exist "%~dp0\backend\.env" (
    for /f "usebackq tokens=1,2 delims==" %%i in ("%~dp0\backend\.env") do (
        if "%%i"=="PORT" set PORT=%%j
        if "%%i"=="HOST" set HOST=%%j
        if "%%i"=="GATEWAY_PREFIX" set PREFIX=%%j
    )
)

set GATEWAY_URL=http://%HOST%:%PORT%%PREFIX%

:: Check if local gateway is running
curl -s -o NUL %GATEWAY_URL%/health
if %errorlevel% neq 0 (
    echo [WARNING] AI Gateway Pro server does not appear to be running on %GATEWAY_URL%
    echo Please run "aig-server.bat" to start the gateway before using Claude Code.
    echo.
    set /p choice="Do you want to launch Claude Code anyway? (y/n): "
    if /i "%choice%" neq "y" exit /b 1
)

:: Route Anthropic client requests to the gateway
set ANTHROPIC_BASE_URL=%GATEWAY_URL%
set ANTHROPIC_API_KEY=sk-ant-aigateway-pro-rotation-key

echo Routing API requests to: %ANTHROPIC_BASE_URL%
echo.

claude %*
