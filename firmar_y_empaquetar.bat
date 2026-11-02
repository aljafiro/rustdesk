@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================================
echo   Firma y Empaquetado Oficial - Soporte Deputacion
echo ==========================================================
echo.

set "ENV_ARG="
if not "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0firmar_y_empaquetar.ps1" %*
    goto :fin
)

echo Selecciona el entorno a empaquetar:
echo   [1] PRE - Preproduccion (por defecto)
echo   [2] PRO - Produccion
echo.
set /p "OPCION=Opcion [1 o 2, ENTER para PRE]: "

if "%OPCION%"=="2" (
    set "ENV_ARG=-Env PRO"
) else (
    set "ENV_ARG=-Env PRE"
)

echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0firmar_y_empaquetar.ps1" %ENV_ARG%

:fin
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] El proceso de firma o empaquetado ha fallado con error %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Proceso finalizado correctamente.
pause
