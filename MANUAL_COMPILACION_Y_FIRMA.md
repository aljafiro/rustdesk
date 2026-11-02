# Manual de Configuración, Compilación, Empaquetado y Firma
## Cliente RustDesk - Deputación da Coruña

Este documento describe en detalle el ciclo completo para configurar los entornos (PRE y PRO), compilar los binarios, empaquetar la versión portable y firmar digitalmente los ejecutables.

---

## 1. Estructura de Entornos y Configuración

Los parámetros de conexión (servidor *rendezvous*, clave pública del servidor, servidor API/CAU y relay forzado) se gestionan de forma centralizada en la carpeta `config/`:

* **`config/pre.json`**: Configuración para el entorno de **Preproducción**.
* **`config/pro.json`**: Configuración para el entorno de **Producción**.

### Formato de archivo (`config/pro.json` o `config/pre.json`):
```json
{
  "environment": "PRO",
  "rendezvous_server": "soporteremoto-diputacion.dacoruna.gal",
  "rendezvous_port": 21116,
  "api_server": "https://soporteremoto-diputacion-cau.dacoruna.gal",
  "key": "<CLAVE_PUBLICA_PRO_AQUI>",
  "forced_relay": "Y"
}
```

### Herramienta automatizadora: `configure_env.py`
Permite aplicar los valores al código fuente antes de compilar o generar los ficheros de configuración portables:

* **Consultar configuración actual:**
  ```bash
  python configure_env.py info pre
  python configure_env.py info pro
  ```

* **Inyectar configuración en el código Rust (`config.rs` y `common.rs`):**
  ```bash
  python configure_env.py apply pre
  python configure_env.py apply pro
  ```

* **Generar `config.toml` para empaquetado:**
  ```bash
  # Para cliente final (sólo entrante):
  python configure_env.py generate-toml pre -o "flutter/build/windows/x64/runner/Release" --incoming-only

  # Para soporte técnico (bidireccional):
  python configure_env.py generate-toml pro -o "flutter/build/windows/x64/runner/Release"
  ```

---

## 2. Tipos de Clientes y Nomenclatura de Ejecutables

En el repositorio se construyen dos variantes del ejecutable según el destinatario y el entorno:

| Tipo | Destinatario | Modo | Nombre en Producción (PRO) | Nombre en Preproducción (PRE) |
| :--- | :--- | :--- | :--- | :--- |
| **Cliente** | Usuario final asistido | `--incoming-only` (sólo recepción) | **`soporte-diputacion.exe`** | **`soporte-diputacion-pre.exe`** |
| **Soporte CAU** | Técnico / Operador CAU | Bidireccional (emisión y recepción) | **`soporte-diputacion-CAU.exe`** | **`soporte-diputacion-CAU-pre.exe`** |

---

## 3. Compilación Automática (Recomendado: GitHub Actions)

La forma más rápida, reproducible y limpia de compilar es a través de los flujos de CI/CD en GitHub:

1. Ve a la pestaña **Actions** del repositorio en GitHub.
2. En el menú lateral izquierdo, selecciona el workflow correspondiente:
   * **`DACORUNA - Build RustDesk Portable Windows - CLI`**: Para el ejecutable del usuario final.
   * **`DACORUNA - Build RustDesk Portable Windows - SOPORTE`**: Para el ejecutable del CAU / técnicos.
3. Haz clic en **Run workflow**.
4. En el desplegable **"Entorno de configuración (PRE o PRO)"**, elige:
   * `PRE` para preproducción.
   * `PRO` para producción.
5. Haz clic en el botón verde **Run workflow**.
6. Al finalizar el job (~15-25 min), descarga el artefacto generado en la sección de descargas del flujo:
   * **Cliente PRE:** `soporte-diputacion-pre.exe`
   * **Cliente PRO:** `soporte-diputacion.exe`
   * **Soporte CAU PRE:** `soporte-diputacion-CAU-pre.exe`
   * **Soporte CAU PRO:** `soporte-diputacion-CAU.exe`

---

## 4. Compilación Local en Windows (Manual)

Si dispones del entorno Windows configurado con Visual Studio C++, Flutter, Rust y Vcpkg:

1. **Aplicar el entorno deseado:**
   ```powershell
   python configure_env.py apply PRE   # o PRO
   ```

2. **Compilar versión CLI (Usuario final):**
   ```powershell
   python build.py --portable --flutter --incoming-only
   ```
   *O versión SOPORTE (Técnico):*
   ```powershell
   python build.py --portable --flutter
   ```

3. Los archivos compilados quedarán en:
   `flutter/build/windows/x64/runner/Release/`

---

## 5. Proceso de Firma Digital y Empaquetado

Para evitar alertas de Windows Defender / SmartScreen y cumplir con las directivas de seguridad corporativas, **todos** los binarios internos (`.exe` y `.dll`) así como el ejecutable contenedor exterior deben estar firmados digitalmente.

### ¿Qué archivo descargar de GitHub Actions?
Cuando compilas en GitHub Actions, se publican varios artefactos. Para poder realizar la firma completa debes descargar el **archivo ZIP con la carpeta portable limpia**:
* Para el cliente: **`rustdesk-true-portable-windows-CLI.zip`**
* Para el soporte CAU: **`rustdesk-true-portable-windows-SOPO.zip`**

> **¿Por qué NO descargar el `.exe` final directamente para firmar?**  
> Porque el `.exe` exterior contiene dentro comprimidos `rustdesk.exe` y más de 12 librerías `.dll` (`librustdesk.dll`, `flutter_windows.dll`, etc.). Si sólo firmas el `.exe` exterior, cuando el usuario lo abra, los archivos internos extraídos no tendrán firma y los antivirus corporativos o políticas EDR los bloquearán. Debes firmar los internos primero y luego empaquetar.

---

### Opción A: Firmar y Empaquetar desde LINUX (Recomendado)

En Linux se utiliza la herramienta estándar **`osslsigncode`** (ya instalada en el sistema) junto con el script automatizado **`firmar_y_empaquetar.sh`**.

1. **Descomprimir la carpeta descargada de GitHub Actions:**
   ```bash
   # Ejemplo para el cliente:
   unzip rustdesk-true-portable-windows-CLI.zip -d Release/SoporteDiputacion-CLI
   ```

2. **Ejecutar la firma y empaquetado:**
   ```bash
   # Para entorno PRE:
   ./firmar_y_empaquetar.sh -d Release/SoporteDiputacion-CLI -e PRE -c /ruta/a/certificado_diputacion.pfx

   # Para entorno PRO:
   ./firmar_y_empaquetar.sh -d Release/SoporteDiputacion-CLI -e PRO -c /ruta/a/certificado_diputacion.pfx
   ```
   *(El script te solicitará la contraseña del certificado `.pfx` de forma segura)*.

3. **Qué hace el script en Linux:**
   * Inyecta la configuración de PRE o PRO (`config.toml`).
   * Recorre la carpeta y firma con SHA-256 y timestamp RFC 3161 cada `.exe` y cada `.dll` interno usando `osslsigncode`.
   * Invoca `package_official_portable.py` para compilar el empaquetador para Windows y comprimir todo en el binario final (`soporte-diputacion-pre.exe`, `soporte-diputacion.exe`, `soporte-diputacion-CAU-pre.exe` o `soporte-diputacion-CAU.exe`).
   * Firma el ejecutable exterior final con `osslsigncode`.
   * Verifica la validez de la firma criptográfica.

---

### Opción B: Firmar y Empaquetar desde WINDOWS

#### Requisitos previos en Windows:
1. **Windows SDK**: Tener instalado `signtool.exe`.
2. **Certificado**: Instalado en el almacén de certificados de Windows (`Cert:\CurrentUser\My`), con el nombre o sujeto que contenga `Deputacion`, o en archivo `.pfx`.

#### Ejecución:
* **Modo interactivo (Doble clic):**
  1. Descomprime la carpeta en `Release/SoporteDiputacion-CLI` o `Release/SoporteDiputacion-SOPO`.
  2. Haz doble clic en **`firmar_y_empaquetar.bat`**.
  3. Elige `1` (PRE) o `2` (PRO).

* **Por línea de comandos (PowerShell):**
  ```powershell
  # PRE:
  .\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRE

  # PRO:
  .\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRO -CertFile "C:\certificados\firma.pfx" -CertPassword "clave"
  ```

---

## 6. Actualización del Icono Corporativo

Si en el futuro se necesita renovar la imagen o logotipo institucional:

1. Sustituye el archivo vectorial en:
   `res/corporate_icon.svg`
2. Ejecuta el script de regeneración de iconos:
   ```bash
   python res/update_branding_icons.py
   ```
3. El script reconstruirá automáticamente:
   * El ejecutable binario `.ico` para Windows (`res/icon.ico` y `flutter/windows/runner/resources/app_icon.ico`) en todos los tamaños (16, 32, 48, 64, 128, 256 px).
   * El icono de la bandeja del sistema (`res/tray-icon.ico`).
   * Los vectores SVG de la interfaz Flutter (`flutter/assets/icon.svg`).
   * Los iconos maestros PNG (`res/icon.png` 512x512 y resoluciones estándar).
