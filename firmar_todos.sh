#!/usr/bin/env bash
# ==============================================================================
# Script para firmar y empaquetar todos los artefactos de RustDesk
# (CLI-PRE, CLI-PRO, SOPO-PRE, SOPO-PRO) solicitando la contraseña una sola vez.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CERT_FILE="/home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12"

if [ ! -f "$CERT_FILE" ]; then
    echo "[!] Error: No se encontró el certificado en $CERT_FILE"
    exit 1
fi

echo "=========================================================="
echo "  Firma y Empaquetado de los 4 artefactos de RustDesk     "
echo "=========================================================="
echo ""
echo "Se van a generar y firmar:"
echo "  1) Cliente PRE:       soporte-diputacion-pre.exe"
echo "  2) Cliente PRO:       soporte-diputacion.exe"
echo "  3) Soporte CAU PRE:   soporte-diputacion-CAU-pre.exe"
echo "  4) Soporte CAU PRO:   soporte-diputacion-CAU.exe"
echo ""

# Parsear argumentos si se pasa contraseña (-p)
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--pass)
            CERT_PASS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$CERT_PASS" ]; then
    read -rsp "Introduce la contraseña del certificado Camerfirma (.p12): " CERT_PASS
    echo ""
    echo ""
fi

if [ -z "$CERT_PASS" ]; then
    echo "[!] Error: La contraseña no puede estar vacía."
    exit 1
fi

export CERT_PASS

TARGETS=(
    "Release/SoporteDiputacion-CLI-PRE:PRE:soporte-diputacion-pre.exe:rustdesk-true-portable-windows-CLI-PRE.zip"
    "Release/SoporteDiputacion-CLI-PRO:PRO:soporte-diputacion.exe:rustdesk-true-portable-windows-CLI-PRO.zip"
    "Release/SoporteDiputacion-SOPO-PRE:PRE:soporte-diputacion-CAU-pre.exe:rustdesk-true-portable-windows-SOPO-PRE.zip"
    "Release/SoporteDiputacion-SOPO-PRO:PRO:soporte-diputacion-CAU.exe:rustdesk-true-portable-windows-SOPO-PRO.zip"
)

echo "[*] Preparando carpetas de release desde artefactos ZIP..."
for entry in "${TARGETS[@]}"; do
    IFS=":" read -r dir env final_exe zip_file <<< "$entry"
    if [ -f "$zip_file" ]; then
        echo "  -> Descomprimiendo $zip_file en $dir..."
        rm -rf "$dir"
        mkdir -p "$dir"
        unzip -q -o "$zip_file" -d "$dir"
    elif [ ! -d "$dir" ]; then
        echo "[!] Error: No se encontró ni el directorio '$dir' ni el archivo '$zip_file'."
        exit 1
    fi
done
echo ""

for entry in "${TARGETS[@]}"; do
    IFS=":" read -r dir env final_exe zip_file <<< "$entry"
    echo "=========================================================="
    echo "[*] Procesando: $final_exe ($env)"
    echo "    Directorio: $dir"
    echo "=========================================================="
    
    ./firmar_y_empaquetar.sh -d "$dir" -e "$env" -c "$CERT_FILE" -p "$CERT_PASS"
    echo ""
done

unset CERT_PASS

echo "=========================================================="
echo "  ¡LOS 4 EJECUTABLES HAN SIDO GENERADOS Y FIRMADOS!       "
echo "=========================================================="
ls -lh soporte-diputacion*.exe
