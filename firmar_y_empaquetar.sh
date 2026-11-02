#!/usr/bin/env bash
# ==============================================================================
# Script de Firma y Empaquetado Oficial de RustDesk en Linux
# Utiliza osslsigncode para firmar binarios PE de Windows (.exe y .dll)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Valores por defecto
RELEASE_DIR=""
ENV="PRE"
CERT_FILE=""
CERT_PASS=""
TIMESTAMP_URL="http://timestamp.digicert.com"

# Función de ayuda
show_help() {
    cat << EOF
Uso: $0 [opciones]

Opciones:
  -d, --dir <directorio>     Carpeta desempaquetada del artefacto (ej: Release/SoporteDiputacion-CLI)
  -e, --env <PRE|PRO>        Entorno a configurar (por defecto: PRE)
  -c, --cert <archivo.pfx>   Ruta al certificado de firma (.pfx o .p12)
  -p, --pass <contraseña>    Contraseña del certificado .pfx (si no se especifica, se preguntará)
  -t, --ts <url>             Servidor de sellado de tiempo RFC 3161 (por defecto: $TIMESTAMP_URL)
  -h, --help                 Muestra esta ayuda

Ejemplo:
  $0 -d ./Release/SoporteDiputacion-CLI -e PRE -c /ruta/a/mi_certificado.pfx
EOF
    exit 0
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--dir)
            RELEASE_DIR="$2"
            shift 2
            ;;
        -e|--env)
            ENV="$(echo "$2" | tr '[:lower:]' '[:upper:]')"
            shift 2
            ;;
        -c|--cert)
            CERT_FILE="$2"
            shift 2
            ;;
        -p|--pass)
            CERT_PASS="$2"
            shift 2
            ;;
        -t|--ts)
            TIMESTAMP_URL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "[!] Opción desconocida: $1"
            show_help
            ;;
    esac
done

echo "=========================================================="
echo "  Firma y Empaquetado Oficial en Linux - Soporte Deputación"
echo "=========================================================="
echo ""

# 1. Comprobar herramientas requeridas
if ! command -v osslsigncode >/dev/null 2>&1; then
    echo "[!] Error: 'osslsigncode' no está instalado en el sistema."
    echo "    Puedes instalarlo en Ubuntu/Debian con: sudo apt install osslsigncode"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] Error: 'python3' no está instalado."
    exit 1
fi

# 2. Localizar directorio de release si no se ha especificado
if [ -z "$RELEASE_DIR" ]; then
    POSSIBLE_DIRS=(
        "Release/SoporteDiputacion-CLI"
        "Release/SoporteDiputacion-SOPO"
        "flutter/build/windows/x64/runner/Release"
        "flutter/build/windows/runner/Release"
    )
    for d in "${POSSIBLE_DIRS[@]}"; do
        if [ -d "$d" ] && [ -f "$d/rustdesk.exe" ]; then
            RELEASE_DIR="$d"
            break
        fi
    done
fi

if [ -z "$RELEASE_DIR" ] || [ ! -d "$RELEASE_DIR" ]; then
    echo "[!] No se encontró ninguna carpeta de release válida."
    read -rp "Introduce la ruta de la carpeta desempaquetada (con rustdesk.exe): " RELEASE_DIR
    if [ ! -d "$RELEASE_DIR" ] || [ ! -f "$RELEASE_DIR/rustdesk.exe" ]; then
        echo "[!] Error: La ruta '$RELEASE_DIR' no existe o no contiene rustdesk.exe."
        exit 1
    fi
fi

echo "[*] Carpeta de origen: $RELEASE_DIR"
echo "[*] Entorno objetivo:   $ENV"

# 3. Localizar certificado PFX
if [ -z "$CERT_FILE" ]; then
    # Buscar si hay un único archivo .pfx en el directorio actual
    PFX_CANDIDATES=(*.pfx *.p12)
    if [ -f "${PFX_CANDIDATES[0]}" ]; then
        CERT_FILE="${PFX_CANDIDATES[0]}"
        echo "[*] Certificado detectado automáticamente: $CERT_FILE"
    else
        read -rp "Introduce la ruta de tu archivo certificado (.pfx o .p12): " CERT_FILE
    fi
fi

if [ ! -f "$CERT_FILE" ]; then
    echo "[!] Error: El archivo de certificado '$CERT_FILE' no existe."
    exit 1
fi

# 4. Solicitar contraseña del certificado si no se proporcionó
if [ -z "$CERT_PASS" ]; then
    read -rsp "Introduce la contraseña del certificado .pfx: " CERT_PASS
    echo ""
fi

# Función auxiliar para firmar un binario con osslsigncode
sign_file() {
    local target="$1"
    local tmp_out="${target}.signed"
    echo "  -> Firmando: $(basename "$target")"

    local pass_param=()
    if [ -n "$CERT_PASS" ]; then
        pass_param=(-pass "$CERT_PASS")
    fi

    osslsigncode sign \
        -pkcs12 "$CERT_FILE" \
        "${pass_param[@]}" \
        -h sha256 \
        -ts "$TIMESTAMP_URL" \
        -in "$target" \
        -out "$tmp_out" >/dev/null 2>&1

    if [ -f "$tmp_out" ]; then
        mv "$tmp_out" "$target"
    else
        echo "[!] Fallo al firmar $target con osslsigncode."
        exit 1
    fi
}

# 5. Generar archivo config.toml según el entorno
echo ""
echo "[PASO 1] Inyectando configuración del entorno [$ENV]..."
CLI_FLAG=""
if [[ "$RELEASE_DIR" =~ "CLI" ]] || [ -d "$RELEASE_DIR/data" ]; then
    CLI_FLAG="--incoming-only"
fi

if [ -f "configure_env.py" ]; then
    python3 configure_env.py generate-toml "$ENV" --output "$RELEASE_DIR" $CLI_FLAG
fi

# 6. Firmar todos los ejecutables y librerías internas
echo ""
echo "[PASO 2] Firmando binarios internos (.exe y .dll) en $RELEASE_DIR..."
while IFS= read -r -d '' bin_file; do
    sign_file "$bin_file"
done < <(find "$RELEASE_DIR" -type f \( -iname "*.exe" -o -iname "*.dll" \) -print0)

echo "[+] Todos los binarios internos han sido firmados correctamente."

# 7. Determinar nombre del ejecutable final
IS_PRE=false
if [ "$ENV" = "PRE" ]; then
    IS_PRE=true
fi

if [[ "$RELEASE_DIR" =~ "SOPO" ]]; then
    if [ "$IS_PRE" = true ]; then
        FINAL_EXE="soporte-diputacion-CAU-pre.exe"
    else
        FINAL_EXE="soporte-diputacion-CAU.exe"
    fi
else
    if [ "$IS_PRE" = true ]; then
        FINAL_EXE="soporte-diputacion-pre.exe"
    else
        FINAL_EXE="soporte-diputacion.exe"
    fi
fi

# 8. Empaquetar ejecutable único portable oficial
echo ""
echo "[PASO 3] Empaquetando ejecutable único portable ($FINAL_EXE)..."
python3 package_official_portable.py "$RELEASE_DIR" "$FINAL_EXE"

if [ ! -f "$FINAL_EXE" ]; then
    echo "[!] Error: No se encontró el ejecutable final $FINAL_EXE tras el empaquetado."
    exit 1
fi

# 9. Firmar el ejecutable único exterior
echo ""
echo "[PASO 4] Firmando el ejecutable contenedor final $FINAL_EXE..."
sign_file "$FINAL_EXE"

echo ""
echo "[+] ¡PROCESO COMPLETADO CON ÉXITO!"
echo "    Ejecutable generado y firmado: $FINAL_EXE"
echo "    - Binarios internos firmados: SÍ"
echo "    - Ejecutable contenedor firmado: SÍ"
echo "    - Sellado de tiempo RFC 3161: SÍ"
echo ""

# 10. Verificación
echo "[*] Verificando firma del ejecutable final con osslsigncode:"
osslsigncode verify "$FINAL_EXE" 2>&1 | grep -E "Signature verification:|Message digest algorithm:|Authenticated attributes:" || true
echo "[OK] Listo para distribuir."
