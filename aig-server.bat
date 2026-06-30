@echo off
title AI Gateway Pro Server
echo ======================================================
echo Starting AI Gateway Pro Server...
echo ======================================================
cd /d "%~dp0\backend"
.venv\Scripts\python run.py
pause
