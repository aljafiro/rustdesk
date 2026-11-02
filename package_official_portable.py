#!/usr/bin/env python3
"""
RustDesk Windows Portable Packager using the Official Self-Extracting Packer.
This script uses RustDesk's native 'libs/portable/generate.py' to produce a single-file,
native self-extracting executable without relying on Enigma Virtual Box.
"""

import os
import sys
import shutil
import subprocess

POSSIBLE_RELEASE_DIRS = [
    os.path.join("flutter", "build", "windows", "x64", "runner", "Release"),
    os.path.join("flutter", "build", "windows", "runner", "Release"),
    os.path.join("build", "windows", "x64", "runner", "Release"),
    os.path.join("target", "release"),
]

FINAL_EXE_NAME = "soporte-diputacion.exe"

def find_release_dir():
    for d in POSSIBLE_RELEASE_DIRS:
        if os.path.exists(d):
            main_exe = os.path.join(d, "rustdesk.exe")
            if os.path.exists(main_exe):
                return d
    return None

def main():
    print("====================================================")
    print("  RustDesk Official Portable Packager               ")
    print("====================================================")

    release_dir = sys.argv[1] if len(sys.argv) > 1 else find_release_dir()
    if not release_dir or not os.path.exists(release_dir):
        print(f"[!] Error: Release directory not found!")
        print(f"Searched in: {POSSIBLE_RELEASE_DIRS}")
        print("Please compile the Windows project first using 'python build.py --portable --flutter'.")
        sys.exit(1)

    main_exe = os.path.join(release_dir, "rustdesk.exe")
    if not os.path.exists(main_exe):
        print(f"[!] Error: 'rustdesk.exe' not found in '{release_dir}'.")
        sys.exit(1)

    print(f"[*] Found Release folder: {release_dir}")

    # Copy Runner.res to libs/portable if available
    runner_res_found = None
    for root, _, files in os.walk("."):
        if "Runner.res" in files:
            runner_res_found = os.path.join(root, "Runner.res")
            break
    if runner_res_found:
        dest_res = os.path.join("libs", "portable", "Runner.res")
        shutil.copyfile(runner_res_found, dest_res)
        print(f"[*] Copied {runner_res_found} -> {dest_res}")

    # Ensure brotli is installed
    try:
        import brotli
    except ImportError:
        print("[*] Installing required python module 'brotli'...")
        subprocess.run([sys.executable, "-m", "pip", "install", "brotli"], check=True)

    # Clean dpiAware in manifest if needed for packer
    manifest_path = os.path.join("res", "manifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()
        if "dpiAware" in manifest_content:
            cleaned_manifest = "\n".join(
                line for line in manifest_content.splitlines() if "dpiAware" not in line
            )
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(cleaned_manifest)
            print("[*] Prepared res/manifest.xml for packaging")

    # Run libs/portable/generate.py
    generator_script = os.path.join("libs", "portable", "generate.py")
    portable_out = os.path.join("libs", "portable")

    cmd = [
        sys.executable,
        generator_script,
        "-f",
        release_dir,
        "-o",
        portable_out,
        "-e",
        main_exe,
    ]

    # En Linux / cross-compilation necesitamos especificar el target de Windows
    if sys.platform != "win32":
        cmd.extend(["-t", "x86_64-pc-windows-gnu"])

    print(f"[*] Executing official packager: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[!] Official packaging failed.")
        sys.exit(result.returncode)

    # Determinar nombre del ejecutable final (soporta argumento opcional o deriva del nombre de la carpeta)
    folder_base = os.path.basename(os.path.normpath(release_dir))
    if len(sys.argv) > 2:
        final_exe_name = sys.argv[2]
        if not final_exe_name.lower().endswith(".exe"):
            final_exe_name += ".exe"
    elif folder_base and folder_base.lower() not in ["release", "runner"]:
        final_exe_name = f"{folder_base}_Portable.exe"
    else:
        final_exe_name = FINAL_EXE_NAME

    # Locate generated binary
    search_paths = [
        os.path.join("target", "x86_64-pc-windows-gnu", "release", "rustdesk-portable-packer.exe"),
        os.path.join("target", "x86_64-pc-windows-msvc", "release", "rustdesk-portable-packer.exe"),
        os.path.join("target", "release", "rustdesk-portable-packer.exe"),
        os.path.join("libs", "portable", "target", "x86_64-pc-windows-gnu", "release", "rustdesk-portable-packer.exe"),
        os.path.join("libs", "portable", "target", "release", "rustdesk-portable-packer.exe"),
    ]

    packer_exe = None
    for p in search_paths:
        if os.path.exists(p):
            packer_exe = p
            break

    if packer_exe:
        shutil.copyfile(packer_exe, final_exe_name)
        print(f"\n[+] SUCCESS! Official portable single-file binary created: '{final_exe_name}'")
        print(f"[*] You can now sign '{final_exe_name}' with osslsigncode/signtool and distribute it.")
    else:
        print(f"[!] Warning: Built package finished but packer binary was not found in: {search_paths}")

if __name__ == "__main__":
    main()
