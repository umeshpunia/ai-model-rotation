@echo off
title Claude Code via AI Gateway
echo ======================================================
echo Launching Claude Code via AI Gateway Pro...
echo ======================================================

:: Check if local gateway is running
curl -s -o NUL http://127.0.0.1:8080/v1/health
if %errorlevel% neq 0 (
    echo [WARNING] AI Gateway Pro server does not appear to be running on http://127.0.0.1:8080
    echo Please run "aig-server.bat" to start the gateway before using Claude Code.
    echo.
    set /p choice="Do you want to launch Claude Code anyway? (y/n): "
    if /i "%choice%" neq "y" exit /b 1
)

:: Route Anthropic client requests to the gateway
set ANTHROPIC_BASE_URL=http://localhost:8080/v1
set ANTHROPIC_API_KEY=sk-ant-aigateway-pro-rotation-key

echo Routing API requests to: %ANTHROPIC_BASE_URL%
echo.

claude %*
