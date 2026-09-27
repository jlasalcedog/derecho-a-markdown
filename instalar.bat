@echo off
chcp 65001 >nul
title Instalar Derecho a Markdown
if not exist "%~dp0instalar.ps1" goto :sinextraer
if not exist "%~dp0app\convertir_markitdown.pyw" goto :sinextraer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1" %*
echo.
pause
exit /b

:sinextraer
echo.
echo   ERROR: parece que estas ejecutando el instalador desde dentro del .zip.
echo   Haz click derecho sobre el .zip ^> "Extraer todo..." y luego ejecuta
echo   instalar.bat desde la carpeta extraida.
echo.
pause
exit /b 1
