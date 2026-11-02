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

### Requisitos previos en la máquina de empaquetado:
1. **Windows SDK**: Tener instalado `signtool.exe` (habitualmente en `C:\Program Files (x86)\Windows Kits\10\bin\...\x64\signtool.exe`).
2. **Certificado de firma de código**:
   * Instalado en el almacén de certificados de Windows (`Cert:\CurrentUser\My` o `Cert:\LocalMachine\My`), con el nombre o sujeto que contenga `Deputacion` (por defecto).
   * O en archivo `.pfx` con contraseña.
3. **Acceso a internet** para el sellado de tiempo (RFC 3161): `http://timestamp.digicert.com`.

### Cómo ejecutar la firma y empaquetado:

#### Método A: Doble clic interactivo (Recomendado)
1. Coloca la carpeta compilada en `Release/SoporteDiputacion-CLI` o `Release/SoporteDiputacion-SOPO` (o en la ruta por defecto de Flutter `flutter/build/windows/x64/runner/Release`).
2. Haz doble clic en **`firmar_y_empaquetar.bat`**.
3. El script te preguntará en pantalla:
   ```text
   Selecciona el entorno a empaquetar:
     [1] PRE - Preproduccion (por defecto)
     [2] PRO - Produccion
   ```
4. Pulsa `1` o `2` y presiona Enter.

#### Método B: Por línea de comandos (PowerShell / CMD)
```powershell
# Empaquetar y firmar para PRE:
.\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRE

# Empaquetar y firmar para PRO:
.\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRO

# Si se usa un archivo PFX externo:
.\firmar_y_empaquetar.ps1 -ReleaseDir "Release/SoporteDiputacion-CLI" -Env PRO -CertFile "C:\certificados\firma_corporativa.pfx" -CertPassword "claveSecreta"
```

### Qué hace este proceso internamente:
1. **Configuración:** Genera el archivo `config.toml` con las URLs y claves correctas de PRE o PRO dentro de la carpeta de release.
2. **Firma Paso 1:** Firma cada archivo individual (`rustdesk.exe` y todas las `.dll` de Flutter y plugins) con SHA-256 y sellado de tiempo.
3. **Empaquetado Paso 2:** Invoca `package_official_portable.py` para comprimir la carpeta firmada en un único archivo ejecutable según el entorno y perfil (`soporte-diputacion-pre.exe`, `soporte-diputacion.exe`, `soporte-diputacion-CAU-pre.exe` o `soporte-diputacion-CAU.exe`).
4. **Firma Paso 3:** Firma el ejecutable exterior final con el mismo certificado y timestamp.

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
