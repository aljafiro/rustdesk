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

read -rsp "Introduce la contraseña del certificado Camerfirma (.p12): " CERT_PASS
echo ""
echo ""

if [ -z "$CERT_PASS" ]; then
    echo "[!] Error: La contraseña no puede estar vacía."
    exit 1
fi

export CERT_PASS

TARGETS=(
    "Release/SoporteDiputacion-CLI-PRE:PRE:soporte-diputacion-pre.exe"
    "Release/SoporteDiputacion-CLI-PRO:PRO:soporte-diputacion.exe"
    "Release/SoporteDiputacion-SOPO-PRE:PRE:soporte-diputacion-CAU-pre.exe"
    "Release/SoporteDiputacion-SOPO-PRO:PRO:soporte-diputacion-CAU.exe"
)

for entry in "${TARGETS[@]}"; do
    IFS=":" read -r dir env final_exe <<< "$entry"
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
