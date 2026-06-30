@echo off
title OpenCode via AI Gateway
echo ======================================================
echo Launching OpenCode via AI Gateway Pro...
echo ======================================================

:: Check if local gateway is running
curl -s -o NUL http://127.0.0.1:8080/v1/health
if %errorlevel% neq 0 (
    echo [WARNING] AI Gateway Pro server does not appear to be running on http://127.0.0.1:8080
    echo Please run "aig-server.bat" to start the gateway before using OpenCode.
    echo.
    set /p choice="Do you want to launch OpenCode anyway? (y/n): "
    if /i "%choice%" neq "y" exit /b 1
)

:: Route OpenCode client requests to the gateway
set OPENAI_BASE_URL=http://localhost:8080/v1
set OPENAI_API_KEY=sk-ant-aigateway-pro-rotation-key

echo Routing API requests to: %OPENAI_BASE_URL%
echo.

opencode %*
