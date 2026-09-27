@echo off
chcp 65001 >nul
title Desinstalar Derecho a Markdown
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0desinstalar.ps1"
echo.
pause
