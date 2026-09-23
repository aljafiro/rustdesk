<#
.SYNOPSIS
    Script para firmar los binarios internos y empaquetar el ejecutable portable oficial de RustDesk (Soporte Deputación)
    sin necesidad de subir el certificado de firma al repositorio de GitHub.

.DESCRIPTION
    Flujo:
    1. Firma todos los binarios internos (.exe y .dll) de la carpeta Release descargada de GitHub Actions.
    2. Ejecuta el empaquetador oficial de RustDesk (libs/portable/generate.py) para empaquetar los binarios ya firmados en un solo ejecutable.
    3. Firma el ejecutable único final (Soporte_Deputacion_Portable.exe).
#>

param (
    [string]$ReleaseDir = "",
    [string]$CertSubject = "Deputacion",  # Nombre o parte del sujeto del certificado instalado en el almacén de Windows
    [string]$CertFile = "",               # Opcional: Ruta a archivo .pfx
    [string]$CertPassword = "",           # Opcional: Contraseña del .pfx
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Firma y Empaquetado Oficial - Soporte Deputación       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Detectar signtool
$signtool = $null
$possibleSigntools = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
)
foreach ($path in $possibleSigntools) {
    if (Test-Path $path) {
        $signtool = $path
        break
    }
}
if (-not $signtool) {
    $found = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($found) { $signtool = $found.Source }
}

if (-not $signtool) {
    Write-Host "[!] Error: No se ha encontrado 'signtool.exe'. Asegúrate de tener instalado el Windows SDK." -ForegroundColor Red
    exit 1
}
Write-Host "[*] SignTool encontrado: $signtool" -ForegroundColor Green

# 2. Localizar la carpeta Release
if (-not $ReleaseDir) {
    $possibleDirs = @(
        "flutter\build\windows\x64\runner\Release",
        "flutter\build\windows\runner\Release",
        "Release",
        "rustdesk-true-portable-windows-SOPO"
    )
    foreach ($d in $possibleDirs) {
        if (Test-Path (Join-Path $d "rustdesk.exe")) {
            $ReleaseDir = $d
            break
        }
    }
}

if (-not $ReleaseDir -or -not (Test-Path $ReleaseDir)) {
    Write-Host "[!] Error: No se ha encontrado la carpeta de binarios Release." -ForegroundColor Red
    Write-Host "    Uso: .\firmar_y_empaquetar.ps1 -ReleaseDir <ruta_carpeta_Release>" -ForegroundColor Yellow
    exit 1
}

Write-Host "[*] Carpeta Release seleccionada: $ReleaseDir" -ForegroundColor Green

# Función auxiliar para firmar con signtool
function Sign-File([string]$FilePath) {
    Write-Host "    Firmando: $FilePath" -ForegroundColor Gray
    if ($CertFile) {
        & $signtool sign /f $CertFile /p $CertPassword /fd sha256 /tr $TimestampServer /td sha256 $FilePath
    } else {
        # Firma usando el certificado instalado en el almacén de Windows (o Token / SmartCard)
        & $signtool sign /n $CertSubject /fd sha256 /tr $TimestampServer /td sha256 $FilePath
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Error al firmar $FilePath" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# 3. Firmar todos los ficheros ejecutables y librerías internas
Write-Host "`n[PASO 1] Firmando binarios internos en $ReleaseDir ..." -ForegroundColor Yellow
$filesToSign = Get-ChildItem -Path $ReleaseDir -Include *.exe, *.dll -Recurse
foreach ($file in $filesToSign) {
    Sign-File $file.FullName
}
Write-Host "[+] Todos los binarios internos (.exe y .dll) han sido firmados correctamente." -ForegroundColor Green

# 4. Generar el ejecutable único con el empaquetador oficial de RustDesk
Write-Host "`n[PASO 2] Empaquetando con el empaquetador nativo de RustDesk ..." -ForegroundColor Yellow
python package_official_portable.py $ReleaseDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Error durante el empaquetado oficial." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Firmar el ejecutable único exterior
$finalExe = "Soporte_Deputacion_Portable.exe"
if (Test-Path $finalExe) {
    Write-Host "`n[PASO 3] Firmando el ejecutable final $finalExe ..." -ForegroundColor Yellow
    Sign-File (Resolve-Path $finalExe).Path
    Write-Host "`n[+] ¡PROCESO COMPLETADO CON ÉXITO!" -ForegroundColor Green
    Write-Host "    Fichero generado y firmado: $finalExe" -ForegroundColor Cyan
    Write-Host "    Tanto el ejecutable exterior como los archivos internos (.dll y .exe) están firmados." -ForegroundColor Cyan
} else {
    Write-Host "[!] Error: No se encontró el ejecutable final $finalExe tras el empaquetado." -ForegroundColor Red
    exit 1
}
