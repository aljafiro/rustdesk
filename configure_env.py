#!/usr/bin/env python3
"""
Script para gestionar la configuración de entornos (PRE y PRO) en RustDesk.
Permite:
  1. Inyectar valores en el código fuente de Rust antes de compilar (`apply`).
  2. Generar el archivo config.toml portable para empaquetado (`generate-toml`).
  3. Consultar valores de configuración (`info` o `get`).
"""

import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")


def load_env_config(env_name: str) -> dict:
    env_clean = env_name.strip().lower()
    json_path = os.path.join(CONFIG_DIR, f"{env_clean}.json")
    if not os.path.exists(json_path):
        print(f"[!] Error: No se encontró el archivo de configuración para el entorno '{env_name}': {json_path}")
        sys.exit(1)
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_to_source(cfg: dict):
    env_name = cfg.get("environment", "UNKNOWN")
    server = cfg.get("rendezvous_server", "").strip()
    port = cfg.get("rendezvous_port", 21116)
    key = cfg.get("key", "").strip()
    api_server = cfg.get("api_server", "").strip()

    print(f"[*] Aplicando configuración del entorno [{env_name}] al código fuente...")
    print(f"    - Rendezvous Server: {server}:{port}")
    print(f"    - API Server:        {api_server}")
    print(f"    - Public Key:        {key}")

    # 1. libs/hbb_common/src/config.rs (resolviendo enlaces simbólicos)
    hbb_candidates = [
        os.path.join(SCRIPT_DIR, "libs", "hbb_common", "src", "config.rs"),
        os.path.join(SCRIPT_DIR, "..", "hbb_common", "src", "config.rs"),
    ]
    seen_files = set()
    hbb_updated = False
    for p in hbb_candidates:
        if os.path.exists(p):
            real_p = os.path.realpath(p)
            if real_p in seen_files:
                continue
            seen_files.add(real_p)

            with open(real_p, "r", encoding="utf-8") as f:
                content = f.read()

            # Reemplazar RENDEZVOUS_SERVERS
            new_content = re.sub(
                r'pub const RENDEZVOUS_SERVERS:\s*&\[&str\]\s*=\s*&\[.*?\];',
                f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{server}"];',
                content,
            )
            # Reemplazar RS_PUB_KEY
            new_content = re.sub(
                r'pub const RS_PUB_KEY:\s*&str\s*=\s*".*?";',
                f'pub const RS_PUB_KEY: &str = "{key}";',
                new_content,
            )

            if new_content != content:
                with open(real_p, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[+] Actualizado correctamente: {p}")
            else:
                print(f"[-] Sin cambios necesarios en: {p}")
            hbb_updated = True

    if not hbb_updated:
        print("[!] Advertencia: No se encontró libs/hbb_common/src/config.rs")

    # 2. src/common.rs
    common_rs_path = os.path.join(SCRIPT_DIR, "src", "common.rs")
    if os.path.exists(common_rs_path):
        with open(common_rs_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        # Actualizar DEFAULT_API_SERVER
        if "DEFAULT_API_SERVER" in new_content:
            new_content = re.sub(
                r'pub const DEFAULT_API_SERVER:\s*&str\s*=\s*".*?";',
                f'pub const DEFAULT_API_SERVER: &str = "{api_server}";',
                new_content,
            )
        else:
            # Reemplazar URL hardcodeada anterior de cau
            new_content = re.sub(
                r'"https://soporteremoto-diputacion-cau-pre\.dacoruna\.gal"',
                f'"{api_server}"',
                new_content,
            )

        if new_content != content:
            with open(common_rs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[+] Actualizado correctamente: {common_rs_path}")
        else:
            print(f"[-] Sin cambios necesarios en: {common_rs_path}")


def generate_toml(cfg: dict, output_dir: str, incoming_only: bool = False):
    server = cfg.get("rendezvous_server", "").strip()
    port = cfg.get("rendezvous_port", 21116)
    key = cfg.get("key", "").strip()
    api_server = cfg.get("api_server", "").strip()
    forced_relay = cfg.get("forced_relay", "Y")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    toml_path = os.path.join(output_dir, "config.toml")
    lines = [
        "[options]",
        f'rendezvous_server = "{server}:{port}"',
        f'api_server = "{api_server}"',
        f'key = "{key}"',
        f'forced_relay = "{forced_relay}"',
    ]
    if incoming_only:
        lines.append('incoming-only = true')

    content = "\n".join(lines) + "\n"
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[+] Archivo config.toml generado en: {toml_path}")
    print(content)


def main():
    parser = argparse.ArgumentParser(description="Gestor de configuración PRE/PRO para RustDesk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: info
    p_info = subparsers.add_parser("info", help="Muestra la información de configuración de un entorno")
    p_info.add_argument("env", choices=["pre", "pro", "PRE", "PRO"], help="Entorno a consultar")

    # Subcomando: get
    p_get = subparsers.add_parser("get", help="Obtiene una clave específica de la configuración")
    p_get.add_argument("env", choices=["pre", "pro", "PRE", "PRO"], help="Entorno")
    p_get.add_argument("key", help="Clave a obtener (ej: rendezvous_server, key, api_server)")

    # Subcomando: apply
    p_apply = subparsers.add_parser("apply", help="Aplica la configuración al código fuente de Rust")
    p_apply.add_argument("env", choices=["pre", "pro", "PRE", "PRO"], help="Entorno a aplicar")

    # Subcomando: generate-toml
    p_toml = subparsers.add_parser("generate-toml", help="Genera config.toml para un entorno")
    p_toml.add_argument("env", choices=["pre", "pro", "PRE", "PRO"], help="Entorno")
    p_toml.add_argument("--output", "-o", required=True, help="Carpeta de destino para config.toml")
    p_toml.add_argument("--incoming-only", action="store_true", help="Activar incoming-only (para cliente)")

    args = parser.parse_args()

    cfg = load_env_config(args.env)

    if args.command == "info":
        print(json.dumps(cfg, indent=2))
    elif args.command == "get":
        val = cfg.get(args.key)
        if val is not None:
            print(val)
        else:
            print(f"[!] Clave '{args.key}' no encontrada", file=sys.stderr)
            sys.exit(1)
    elif args.command == "apply":
        apply_to_source(cfg)
    elif args.command == "generate-toml":
        generate_toml(cfg, args.output, args.incoming_only)


if __name__ == "__main__":
    main()
