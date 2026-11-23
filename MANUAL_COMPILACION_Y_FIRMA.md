# Manual de Compilación, Empaquetado y Firma Digital
## Cliente RustDesk - Deputación da Coruña

Este documento describe el flujo completo para la generación, empaquetado y firma digital de los ejecutables portables de RustDesk adaptados para la **Deputación da Coruña**.

---

## 1. Nomenclatura y Tipos de Ejecutables

Se generan dos tipos de ejecutables según el destinatario y el entorno objetivo:

| Tipo | Destinatario | Modo | Nombre en Producción (PRO) | Nombre en Preproducción (PRE) |
| :--- | :--- | :--- | :--- | :--- |
| **Cliente** | Usuario final asistido | `--incoming-only` (sólo recepción) | **`soporte-diputacion.exe`** | **`soporte-diputacion-pre.exe`** |
| **Soporte CAU** | Técnico / Operador CAU | Bidireccional (emisión y recepción) | **`soporte-diputacion-CAU.exe`** | **`soporte-diputacion-CAU-pre.exe`** |

---

## 2. ¿Por qué es necesario firmar "por dentro y por fuera"?

Los ejecutables finales (`soporte-diputacion.exe`, `soporte-diputacion-CAU.exe`) son **contenedores portables autoextraíbles** (SFX) generados por el empaquetador oficial de RustDesk:

1. **Firma interna ("por dentro"):**
   * El paquete contiene comprimidos el ejecutable principal `rustdesk.exe` y más de 12 librerías dinámicas (`librustdesk.dll`, `flutter_windows.dll`, decodificadores de video, pantalla virtual, etc.).
   * Al ejecutarse en el equipo del usuario, estos ficheros se descomprimen en el directorio temporal (`%TEMP%`).
   * Si únicamente se firma el archivo `.exe` exterior, los archivos extraídos no tendrán firma digital. Las políticas de seguridad corporativas, Windows Defender SmartScreen y las soluciones EDR/antivirus bloquearán la ejecución de estas librerías sin firmar.
   * **Solución:** Se deben firmar individualmente `rustdesk.exe` y todos los `.dll` antes de empaquetar.

2. **Firma exterior ("por fuera"):**
   * El archivo `.exe` contenedor resultante debe firmarse para que el sistema operativo Windows y el navegador web confíen en el ejecutable durante la descarga y primer inicio.

---

## 3. Fase 1: Compilación en GitHub Actions

La compilación se realiza de forma automatizada en runners Windows de GitHub Actions:

1. Accede a la pestaña **Actions** en el repositorio GitHub (`aljafiro/rustdesk`).
2. Selecciona el workflow deseado:
   * **`DACORUNA - Build RustDesk Portable Windows - CLI`**: Para el cliente de usuario final.
   * **`DACORUNA - Build RustDesk Portable Windows - SOPORTE`**: Para el cliente de técnicos del CAU.
3. Pulsa en **Run workflow**.
4. Selecciona el entorno deseado:
   * **`PRE`**: Apunta a servidores de preproducción (`soporteremoto-diputacion-pre.dacoruna.gal`).
   * **`PRO`**: Apunta a servidores de producción (`soporteremoto-diputacion.dacoruna.gal`).
5. Pulsa el botón verde **Run workflow** y espera a que termine el trabajo (~15 min).

### Artefacto a Descargar (¡IMPORTANTE!)
Para poder realizar la firma completa (interna + externa), **NO** descargues el `.exe` suelto. Debes descargar el **archivo ZIP con la carpeta portable completa**:
* Para cliente: **`rustdesk-true-portable-windows-CLI.zip`**
* Para soporte CAU: **`rustdesk-true-portable-windows-SOPO.zip`**

---

## 4. Fase 2: Firma y Empaquetado

### Opción A: Desde LINUX con `osslsigncode` (Método Recomendado)

Nuestro entorno Linux dispone de la herramienta **`osslsigncode`** y del certificado corporativo en `/home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12`.

#### Paso 1: Descomprimir el artefacto en `Release/`
```bash
cd /home/sdkuser/git/aljafiro/rustdesk

# Si vas a firmar el Cliente:
unzip rustdesk-true-portable-windows-CLI.zip -d Release/SoporteDiputacion-CLI

# Si vas a firmar el Soporte CAU:
unzip rustdesk-true-portable-windows-SOPO.zip -d Release/SoporteDiputacion-SOPO
```

#### Paso 2: Ejecutar el script automatizado `firmar_y_empaquetar.sh`
```bash
# Para cliente en PRE:
./firmar_y_empaquetar.sh \
  -d Release/SoporteDiputacion-CLI \
  -e PRE \
  -c /home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12

# Para cliente en PRO:
./firmar_y_empaquetar.sh \
  -d Release/SoporteDiputacion-CLI \
  -e PRO \
  -c /home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12

# Para soporte CAU en PRE:
./firmar_y_empaquetar.sh \
  -d Release/SoporteDiputacion-SOPO \
  -e PRE \
  -c /home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12

# Para soporte CAU en PRO:
./firmar_y_empaquetar.sh \
  -d Release/SoporteDiputacion-SOPO \
  -e PRO \
  -c /home/sdkuser/Sign/Camerfirma-CodeSign-2024.p12
```
> El script solicitará la contraseña del certificado `.p12` de forma segura por terminal.

#### ¿Qué realiza el script automáticamente?
1. **Inyección de configuración:** Genera `config.toml` adaptado al entorno (servidores rendezvous, relay y API sin `/api`).
2. **Firma interna:** Recorre la carpeta y firma con SHA-256 y sellado de tiempo RFC 3161 cada `.exe` y `.dll`.
3. **Empaquetado:** Invoca `package_official_portable.py` para construir el ejecutable portable final.
4. **Firma exterior:** Firma el contenedor ejecutable final con `osslsigncode`.
5. **Verificación:** Valida criptográficamente el resultado con `osslsigncode verify`.

---

### Opción B: Desde una máquina WINDOWS con `signtool.exe`

Si prefieres realizar la firma en un puesto de trabajo Windows:

#### Requisitos:
1. Tener instalado el **Windows SDK** (incluye `signtool.exe`).
2. Disponer del certificado digital instalado en el almacén personal de Windows (`Cert:\CurrentUser\My`) o en un archivo `.pfx` / `.p12`.

#### Ejecución:
1. Copia la carpeta descomprimida (`Release/SoporteDiputacion-CLI` o `Release/SoporteDiputacion-SOPO`) al equipo Windows.
2. **Método gráfico interactivo:**
   * Haz doble clic en **`firmar_y_empaquetar.bat`**.
   * Elige la opción del entorno (`1` para PRE o `2` para PRO).
3. **Método por PowerShell:**
   ```powershell
   # Firma usando el almacén de Windows:
   .\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRE

   # O especificando archivo PFX y contraseña:
   .\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRO -CertFile "C:\certificados\firma.pfx" -CertPassword "clave"
   ```

---

## 5. Parámetros de Red y Servidores

Las configuraciones base de conexión se encuentran centralizadas en `config/`:
* **`config/pre.json`**:
  ```json
  {
    "environment": "PRE",
    "rendezvous_server": "soporteremoto-diputacion-pre.dacoruna.gal",
    "rendezvous_port": 21116,
    "api_server": "https://soporteremoto-diputacion-cau-pre.dacoruna.gal",
    "key": "mOmm0h89VKDmiGXdlpu/890jmPH4VYYvbbZTIovjSTk=",
    "forced_relay": "Y"
  }
  ```
* **`config/pro.json`**:
  ```json
  {
    "environment": "PRO",
    "rendezvous_server": "soporteremoto-diputacion-pre.dacoruna.gal",
    "rendezvous_port": 21116,
    "api_server": "https://soporteremoto-diputacion-cau-pre.dacoruna.gal",
    "key": "mOmm0h89VKDmiGXdlpu/890jmPH4VYYvbbZTIovjSTk=",
    "forced_relay": "Y"
  }
  ```

> **Nota técnica sobre `api_server`:**  
> La URL del servidor API debe definirse **siempre sin el sufijo `/api`** (`https://...dacoruna.gal`). El cliente RustDesk concatena internamente `/api/...` a todos los endpoints de autenticación y sincronización (ej: `{api_server}/api/oidc/auth`).
