@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Firma y Empaquetado Oficial - Soporte Deputacion
echo ==========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0firmar_y_empaquetar.ps1" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] El proceso de firma o empaquetado ha fallado con error %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Proceso finalizado correctamente.
pause
