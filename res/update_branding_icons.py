#!/usr/bin/env python3
"""
Script para generar e integrar los iconos corporativos en todos los formatos
y rutas requeridas por RustDesk (Windows ICO, Tray ICO, PNGs maestros, UI SVGs).
"""

import os
import re
import struct
import subprocess
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUSTDESK_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CORP_SVG = os.path.join(SCRIPT_DIR, "corporate_icon.svg")


def make_square_svg(inner_paths_str: str, size: int) -> str:
    # Canvas de 72x72 con fondo blanco redondeado para máxima visibilidad en fondos oscuros y claros
    # El escudo original tiene 38x68. Con escala 0.82 queda en 31.16 x 55.76 centrado en 72x72
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 72 72" fill="none">
  <rect x="2" y="2" width="68" height="68" rx="15" ry="15" fill="#FFFFFF"/>
  <g transform="translate(20.42, 8.12) scale(0.82)">
{inner_paths_str}
  </g>
</svg>"""


def build_ico(png_sizes_and_data: list) -> bytes:
    """Construye un archivo binario .ico de Windows con entradas PNG."""
    header = struct.pack("<HHH", 0, 1, len(png_sizes_and_data))
    entries = []
    offset = 6 + 16 * len(png_sizes_and_data)
    chunks = []

    for s, data in png_sizes_and_data:
        w_byte = 0 if s == 256 else s
        h_byte = 0 if s == 256 else s
        size = len(data)
        entry = struct.pack("<BBBBHHII", w_byte, h_byte, 0, 0, 1, 32, size, offset)
        entries.append(entry)
        chunks.append(data)
        offset += size

    return header + b"".join(entries) + b"".join(chunks)


def main():
    if not os.path.exists(CORP_SVG):
        print(f"[!] Error: No se encontró el archivo de icono corporativo: {CORP_SVG}")
        sys.exit(1)

    with open(CORP_SVG, "r", encoding="utf-8") as f:
        svg_raw = f.read()

    # Extraer todos los elementos path
    paths = re.findall(r"<path.*?>", svg_raw, re.DOTALL)
    if not paths:
        print("[!] Error: No se pudieron extraer los paths del SVG.")
        sys.exit(1)

    inner_paths = "\n".join(paths)

    # 1. Generar PNGs en resoluciones estándar
    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    tmp_dir = "/tmp/rustdesk_branding_gen"
    os.makedirs(tmp_dir, exist_ok=True)

    png_cache = {}
    for s in sizes:
        svg_content = make_square_svg(inner_paths, s)
        svg_tmp = os.path.join(tmp_dir, f"icon_{s}.svg")
        png_tmp = os.path.join(tmp_dir, f"icon_{s}.png")
        with open(svg_tmp, "w", encoding="utf-8") as f:
            f.write(svg_content)

        cmd = ["ffmpeg", "-y", "-i", svg_tmp, png_tmp]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            print(f"[!] Error generando PNG para tamaño {s}")
            sys.exit(res.returncode)

        with open(png_tmp, "rb") as f:
            png_cache[s] = f.read()

    # 2. Generar res/icon.png (512x512)
    master_png_path = os.path.join(SCRIPT_DIR, "icon.png")
    with open(master_png_path, "wb") as f:
        f.write(png_cache[512])
    print(f"[+] Actualizado icono maestro PNG (512x512): {master_png_path}")

    # 3. Generar iconos individuales de res/
    for s, name in [(16, "16x16.png"), (32, "32x32.png"), (64, "64x64.png"), (128, "128x128.png")]:
        p = os.path.join(SCRIPT_DIR, name)
        with open(p, "wb") as f:
            f.write(png_cache[s])
        print(f"[+] Actualizado {p}")

    # 4. Generar res/icon.ico multi-resolución (16, 32, 48, 64, 128, 256)
    ico_entries = [(s, png_cache[s]) for s in [16, 32, 48, 64, 128, 256]]
    ico_data = build_ico(ico_entries)

    res_ico_path = os.path.join(SCRIPT_DIR, "icon.ico")
    with open(res_ico_path, "wb") as f:
        f.write(ico_data)
    print(f"[+] Actualizado icono de ejecutable Windows: {res_ico_path}")

    # 5. Generar res/tray-icon.ico (16, 32, 48)
    tray_ico_entries = [(s, png_cache[s]) for s in [16, 32, 48]]
    tray_ico_data = build_ico(tray_ico_entries)
    tray_ico_path = os.path.join(SCRIPT_DIR, "tray-icon.ico")
    with open(tray_ico_path, "wb") as f:
        f.write(tray_ico_data)
    print(f"[+] Actualizado icono de bandeja del sistema (systray): {tray_ico_path}")

    # 6. Actualizar flutter/windows/runner/resources/app_icon.ico
    flutter_ico_path = os.path.join(RUSTDESK_DIR, "flutter", "windows", "runner", "resources", "app_icon.ico")
    if os.path.exists(os.path.dirname(flutter_ico_path)):
        with open(flutter_ico_path, "wb") as f:
            f.write(ico_data)
        print(f"[+] Actualizado icono de Flutter Runner Windows: {flutter_ico_path}")

    # 7. Actualizar flutter/assets/icon.svg (SVG centrado y optimizado para UI)
    ui_svg_content = make_square_svg(inner_paths, 72)
    flutter_svg_path = os.path.join(RUSTDESK_DIR, "flutter", "assets", "icon.svg")
    with open(flutter_svg_path, "w", encoding="utf-8") as f:
        f.write(ui_svg_content)
    print(f"[+] Actualizado icono vectorial UI en Flutter: {flutter_svg_path}")

    # 8. Actualizar res/scalable.svg
    res_scalable_path = os.path.join(SCRIPT_DIR, "scalable.svg")
    with open(res_scalable_path, "w", encoding="utf-8") as f:
        f.write(ui_svg_content)
    print(f"[+] Actualizado SVG escalable: {res_scalable_path}")

    # 9. Actualizar carpetas Release precompiladas si existen
    for rel_folder in ["SoporteDiputacion-CLI", "SoporteDiputacion-SOPO"]:
        rel_base = os.path.join(RUSTDESK_DIR, "Release", rel_folder)
        if os.path.exists(rel_base):
            target_assets_dir = os.path.join(rel_base, "data", "flutter_assets", "assets")
            os.makedirs(target_assets_dir, exist_ok=True)

            target_asset_svg = os.path.join(target_assets_dir, "icon.svg")
            with open(target_asset_svg, "w", encoding="utf-8") as f:
                f.write(ui_svg_content)
            print(f"[+] Actualizado icon.svg en Release: {target_asset_svg}")

            target_asset_ico = os.path.join(target_assets_dir, "icon.ico")
            with open(target_asset_ico, "wb") as f:
                f.write(ico_data)
            print(f"[+] Actualizado icon.ico en Release: {target_asset_ico}")

    print("\n[OK] ¡Todos los iconos han sido actualizados con la identidad corporativa!")


if __name__ == "__main__":
    main()
